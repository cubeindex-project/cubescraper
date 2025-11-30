import argparse
import asyncio
import logging
from collections import defaultdict
from urllib.parse import urlparse

from rich.logging import RichHandler

from cubescraper.common.http import async_fetch_web_page
from cubescraper.price_tracker.constants import SUPPORTED_VENDORS
from cubescraper.price_tracker.parser import parse_url, prepare_update_payload
from cubescraper.price_tracker.price_types import CubeVendorLink, ParseResult
from cubescraper.price_tracker.queries import fetch_vendor_links, update_vendor_link

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[RichHandler()],
)
logger = logging.getLogger(__name__)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("supabase").setLevel(logging.WARNING)

stats = {"changed": 0, "unchanged": 0, "skipped": 0}

DEFAULT_PER_DOMAIN_LIMIT = 3
domain_semaphores = defaultdict(lambda: asyncio.Semaphore(DEFAULT_PER_DOMAIN_LIMIT))


def get_semaphore_for_url(url: str) -> asyncio.Semaphore:
    domain = (urlparse(url).hostname or "").lower()
    return domain_semaphores[domain]


def is_supported(url: str) -> bool:
    domain = (urlparse(url).hostname or "").lower()
    return any(
        domain.endswith(vendor_url)
        for vendor_url, vendor_parser in SUPPORTED_VENDORS.items()
    )


async def process_link(row: CubeVendorLink):
    id_ = row["id"]
    link = row["url"]
    old_price = row.get("price")
    old_availability = row.get("available")

    logger.info("Processing link id=%s url=%s", id_, link)

    if not is_supported(link):
        logger.info("Skipping unsupported link url=%s", link)
        stats["skipped"] += 1
        return

    html = await async_fetch_web_page(link)
    if html is None:
        logger.warning("No HTML fetched for url=%s — skipping", link)
        stats["skipped"] += 1
        return

    parse_result: ParseResult = parse_url(link, html, debug=args.debug)

    if parse_result.availability is None:
        logger.warning("Availability not found for url=%s", link)
        parse_result.availability = old_availability
    if parse_result.price is None:
        logger.warning("Price not found for url=%s", link)
        parse_result.price = old_price

    # Determine whether anything changed
    changed = False
    if parse_result.price != old_price:
        logger.info(
            "Price changed for id=%s: %r -> %r", id_, old_price, parse_result.price
        )
        changed = True
    if parse_result.availability != old_availability:
        logger.info(
            "Availability changed for id=%s: %r -> %r",
            id_,
            old_availability,
            parse_result.availability,
        )
        changed = True

    if not changed:
        logger.debug("No change for id=%s — price or availability same", id_)
        stats["unchanged"] += 1
    else:
        stats["changed"] += 1

    logger.debug("Preparing update payload for id=%s", id_)
    payload = prepare_update_payload(
        id=id_, price=parse_result.price, availability=parse_result.availability
    )

    logger.debug("Updating row in DB for id=%s", id_)
    await update_vendor_link(payload, commit=args.commit)

    # Optionally log the parse result for debugging
    logger.debug("Parse result for url=%s → %r", link, parse_result)


async def process_link_semi(row: CubeVendorLink):
    semaphore = get_semaphore_for_url(row["url"])
    async with semaphore:
        await process_link(row)


async def main():
    logger.info("Fetching vendor rows from DB...")
    vendor_link_rows = await fetch_vendor_links()
    count = len(vendor_link_rows)
    logger.info("Fetched %d vendor row(s)", count)
    if count == 0:
        logger.warning("No vendor links to process — exiting")
        return

    tasks = [process_link_semi(r) for r in vendor_link_rows]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle exceptions if any
    for idx, res in enumerate(results):
        if isinstance(res, Exception):
            logger.error(
                "Task %d (url=%s) raised exception: %s",
                idx,
                vendor_link_rows[idx].get("url"),
                res,
                exc_info=True,
            )

    logger.info(
        "Done: changed=%d, unchanged=%d, skipped=%d",
        stats["changed"],
        stats["unchanged"],
        stats["skipped"],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Cube price fetcher",
        description="Fetch price & availability for known vendor links and update DB.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Verbose log output.",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually commit updates to the database (default: dry-run).",
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger(__name__).setLevel(logging.DEBUG)

    asyncio.run(main())
