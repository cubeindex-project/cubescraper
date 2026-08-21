import argparse
import asyncio
import logging
import random
import time
from collections import defaultdict
from uuid import UUID

import httpx

from cubescraper.common.database_types import PublicCubeVendorLinks
from cubescraper.common.http import async_fetch_web_page
from cubescraper.common.logging import log_context, setup_logging
from cubescraper.common.utils import (
    get_hostname,
    get_short_uuid,
    non_negative_float,
    non_negative_int,
)
from cubescraper.price_tracker.constants import (
    DEAD_LINK_EXCEPTIONS,
    DEAD_LINK_STATUS_CODES,
)
from cubescraper.price_tracker.parser import parse_url, prepare_update_payload
from cubescraper.price_tracker.price_types import ParseResult
from cubescraper.price_tracker.queries import (
    fetch_vendor_links,
    get_enabled_vendors,
    update_vendor_link,
    update_vendor_link_dead_status,
)

DEFAULT_PER_DOMAIN_LIMIT = 1
DEFAULT_PER_DOMAIN_DELAY = 2.0

logger = logging.getLogger(__name__)

stats = {"changed": 0, "unchanged": 0, "skipped": 0, "failed": 0}
domain_semaphores: defaultdict[str, asyncio.Semaphore] | None = None
domain_rate_locks: defaultdict[str, asyncio.Lock] | None = None
domain_last_request_at: dict[str, float] = {}


def get_semaphore_for_url(url: str) -> asyncio.Semaphore:
    if domain_semaphores is None:
        raise RuntimeError("domain semaphores were not initialized")
    domain = (get_hostname(url) or "").lower()
    return domain_semaphores[domain]


async def wait_for_rate_limit(
    url: str, per_domain_delay: float = DEFAULT_PER_DOMAIN_DELAY
):
    if domain_rate_locks is None:
        raise RuntimeError("domain rate locks were not initialized")

    domain = (get_hostname(url) or "").lower()
    async with domain_rate_locks[domain]:
        now = time.monotonic()
        delay = random.uniform(per_domain_delay * 0.5, per_domain_delay * 1.5)
        wait = delay - (now - domain_last_request_at.get(domain, 0))
        if wait > 0:
            logger.info(
                "Waiting %.2f seconds for rate limit on domain %s", wait, domain
            )
            await asyncio.sleep(wait)
        domain_last_request_at[domain] = time.monotonic()


def is_link_dead(exception: Exception) -> bool:
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code in DEAD_LINK_STATUS_CODES

    return isinstance(exception, DEAD_LINK_EXCEPTIONS)


def is_supported(
    url: str,
    supported_vendors: list[str],
) -> bool:
    supported_vendor_hosts = {
        (get_hostname(url) or url).lower() for url in supported_vendors
    }
    vendor_hostname = (get_hostname(url) or "").lower()
    return any(
        vendor_hostname.endswith(supported_vendor_host)
        for supported_vendor_host in supported_vendor_hosts
    )


def remove_unsupported_vendors(
    vendor_links_rows: list[PublicCubeVendorLinks],
    supported_vendors: list[str],
) -> list[PublicCubeVendorLinks]:
    final_list = []
    for vendor_links_row in vendor_links_rows:
        if is_supported(vendor_links_row.url, supported_vendors):
            final_list.append(vendor_links_row)
        else:
            stats["skipped"] += 1

    return final_list


def remove_dead_links(
    vendor_links_rows: list[PublicCubeVendorLinks],
) -> list[PublicCubeVendorLinks]:
    final_list: list[PublicCubeVendorLinks] = []
    for row in vendor_links_rows:
        if row.is_dead:
            stats["skipped"] += 1
        else:
            final_list.append(row)

    return final_list


async def scrape_vendor_link(url: str) -> ParseResult:
    html = await async_fetch_web_page(url, follow_redirects=False)
    if not html:
        raise RuntimeError(f"Failed to fetch web page: {url}")

    return parse_url(url, html)


async def autofill_price(job_id: UUID, job_link: str) -> ParseResult:
    short_job_id = get_short_uuid(job_id)
    token = log_context.set(f"job_id={short_job_id}")
    try:
        logger.info("Next job fetched! url=%s", job_link)
        try:
            price_details = await scrape_vendor_link(job_link)

        except Exception:
            logger.exception("Job failed url=%s", job_link)
            raise

        logger.info(
            "Job completed successfully!",
        )
        logger.debug("Job output: %s", price_details)
        return price_details
    finally:
        log_context.reset(token)


async def refresh_vendor_link(
    row: PublicCubeVendorLinks,
    commit: bool = False,
    per_domain_delay: float = DEFAULT_PER_DOMAIN_DELAY,
):
    token = log_context.set(f"link_id={row.id}")
    try:
        link_id = row.id
        link = row.url
        old_price = row.price
        old_availability = row.available

        logger.info("Processing link id=%s url=%s", link_id, link)

        try:
            await wait_for_rate_limit(link, per_domain_delay)
            parse_result = await scrape_vendor_link(link)

            if parse_result.availability is None or parse_result.price is None:
                raise ValueError(
                    "Parser did not return complete price data: "
                    + f"price={parse_result.price!r}, availability={parse_result.availability!r}"
                )
        except Exception as exc:
            logger.exception(
                "An error occurred while fetching url=%s.",
                link,
            )
            if is_link_dead(exc):
                logger.info("Marking link as dead.")
                await update_vendor_link_dead_status(
                    link_id, is_dead=True, commit=commit
                )
            stats["failed"] += 1
            return

        changed = False
        if parse_result.price != old_price:
            logger.info(
                "Price changed: %r -> %r",
                old_price,
                parse_result.price,
            )
            changed = True
        if parse_result.availability != old_availability:
            logger.info(
                "Availability changed: %r -> %r",
                old_availability,
                parse_result.availability,
            )
            changed = True

        logger.debug("Preparing update payload")
        payload = prepare_update_payload(
            id=link_id, price=parse_result.price, availability=parse_result.availability
        )

        logger.debug("Updating row in DB")
        await update_vendor_link(payload, commit=commit)

        if changed:
            stats["changed"] += 1
        else:
            logger.debug("No change: price and availability same")
            stats["unchanged"] += 1

        logger.info("Finished processing link id=%s url=%s", link_id, link)
    finally:
        log_context.reset(token)


async def refresh_vendor_link_limited(
    row: PublicCubeVendorLinks,
    commit: bool = False,
    per_domain_delay: float = DEFAULT_PER_DOMAIN_DELAY,
):
    semaphore = get_semaphore_for_url(row.url)
    async with semaphore:
        await refresh_vendor_link(row, commit, per_domain_delay)


async def main(
    limit: int | None = None,
    per_domain_limit: int = DEFAULT_PER_DOMAIN_LIMIT,
    commit: bool = False,
    per_domain_delay: float = DEFAULT_PER_DOMAIN_DELAY,
):
    global domain_semaphores, domain_rate_locks
    stats.update(dict.fromkeys(stats, 0))
    domain_semaphores = defaultdict(lambda: asyncio.Semaphore(per_domain_limit))
    domain_rate_locks = defaultdict(asyncio.Lock)
    domain_last_request_at.clear()

    logger.info("Fetching vendor rows from DB...")
    vendor_link_rows = await fetch_vendor_links()
    count = len(vendor_link_rows)
    logger.info("Fetched %d vendor row(s)", count)
    if count == 0:
        logger.warning("No vendor links to process: exiting")
        return

    logger.info("Fetching supported vendors")
    supported_vendors = await get_enabled_vendors()
    logger.info(
        "%d vendor(s) supported: removing unsupported ones", len(supported_vendors)
    )

    vendor_link_rows = remove_unsupported_vendors(vendor_link_rows, supported_vendors)
    logger.info(
        "Unsupported vendors were removed: %s remained",
        len(vendor_link_rows),
    )

    vendor_link_rows = remove_dead_links(vendor_link_rows)
    logger.info(
        "Dead links were removed: %s remained.",
        len(vendor_link_rows),
    )

    if limit is not None:
        vendor_link_count = len(vendor_link_rows)
        stats["skipped"] += max(0, vendor_link_count - limit)
        logger.info(
            "Applied limit of %d: keeping %d of the %d links",
            limit,
            limit,
            vendor_link_count,
        )
        vendor_link_rows = vendor_link_rows[:limit]

    tasks = [
        refresh_vendor_link_limited(r, commit, per_domain_delay)
        for r in vendor_link_rows
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for result in results:
        if isinstance(result, Exception):
            stats["failed"] += 1
            logger.exception("Uncaught task error", exc_info=result)

    logger.info(
        "Done: changed=%d, unchanged=%d, skipped=%d, failed=%d",
        stats["changed"],
        stats["unchanged"],
        stats["skipped"],
        stats["failed"],
    )


if __name__ == "__main__":
    setup_logging(rich_tracebacks=False)

    parser = argparse.ArgumentParser(
        "Cube price fetcher",
        description="Fetch price & availability for known vendor links and update DB.",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually commit updates to the database (default: dry-run).",
    )
    parser.add_argument(
        "--limit",
        type=non_negative_int,
        help="Limit the number of links processed for development",
    )
    parser.add_argument(
        "--per-domain-limit",
        default=DEFAULT_PER_DOMAIN_LIMIT,
        type=non_negative_int,
        help="The number of links processed at the same time for the same domain",
    )
    parser.add_argument(
        "--per-domain-delay",
        default=DEFAULT_PER_DOMAIN_DELAY,
        type=non_negative_float,
        help="The wait time between two processed links of the same domain",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Verbose log output.",
    )

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Log level set to DEBUG")
    else:
        logger.setLevel(logging.INFO)

    started_at = time.perf_counter()
    try:
        asyncio.run(
            main(
                args.limit,
                args.per_domain_limit,
                args.commit,
                args.per_domain_delay,
            )
        )
    finally:
        elapsed = time.perf_counter() - started_at
        logger.info("Finished in %.2f seconds", elapsed)
