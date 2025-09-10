"""
Cube price fetcher
------------------

High-level flow:
- Load due vendor links from Supabase (or all with --force).
- For each link, politely fetch the product page with throttling and retries.
- Prefer parsing JSON-LD Product data; fall back to lightweight HTML heuristics
  and vendor-specific helpers when available.
- Decide availability by combining HTTP status with parsed signals.
- Update the cube_vendor_links row with price, availability, and cache headers.
- Track a per-link backoff based on an unchanged streak to reduce churn.

Notes:
- Per-vendor throttling ensures we don't hammer the same host; different vendors
  can run concurrently.
- Conditional requests (ETag/Last-Modified) reduce bandwidth and parsing when
  pages are unchanged (304 Not Modified).
- Rich console output provides progress + a summary table of changes.
"""

import sys, os, argparse, json, logging, re, asyncio, time, random
import unicodedata
from email.utils import parsedate_to_datetime
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import datetime as dt
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

# allow "src.common.supabaseClient" import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.common.supabaseClient import supabase  # noqa: E402

# ---- Pretty console (always-on progress) ------------------------------------
from rich.console import Console
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.logging import RichHandler

console = Console()

# ---- Supported vendors (hostname fragments) ----
# Domains we actively parse/support; unknown hosts are skipped early
SUPPORTED_VENDORS = [
    "thecubicle.com",
    "gancube.com",
    "speedcubeshop.com",
    "speedcubes.co.za",
]

# ---- Throttling & cooldown config -------------------------------------------
# Minimum time between requests per vendor host (politeness budget)
VENDOR_MIN_INTERVAL = {
    "thecubicle.com": 5.0,
    "gancube.com": 8.0,
    "speedcubeshop.com": 6.0,
    "speedcubes.co.za": 6.0,
}
DEFAULT_MIN_INTERVAL = 8.0
# Add a tiny random jitter so parallel workers don't align perfectly
JITTER_RANGE = (0.0, 0.4)  # seconds

# Skip rows updated too recently
LINK_COOLDOWN = timedelta(hours=12)

# Backoff grows as 12h * 2^streak and is capped to avoid going unbounded
BACKOFF_EXP_CAP = 4  # stop doubling after 2^4 (tweak as you like)
MAX_LINK_COOLDOWN = timedelta(hours=96)  # clamp at 4 days (tweak as you like)
WORKER_CONCURRENCY = 10

last_hit_at = defaultdict(lambda: 0.0)
# One asyncio.Lock per vendor to serialize requests to the same host
vendor_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


# ---- CLI --------------------------------------------------------------------
parser = argparse.ArgumentParser(
    "fetch_cube_price",
    description="Fetch price & availability for known vendor links and update DB.",
)
# Logging is optional:
parser.add_argument("--log", action="store_true", help="Enable pretty INFO logs.")
parser.add_argument("--debug", action="store_true", help="Enable DEBUG logs.")
# Optionally persist fetched HTML locally for debugging the parsers
parser.add_argument(
    "--save-html",
    action="store_true",
    help="Save fetched HTML to ./.debug/<vendor>/<cube>.html",
)


# Require positive integers for --limit
def positive_int(value: str) -> int:
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("limit must be > 0")
    return ivalue


parser.add_argument(
    "--limit",
    type=positive_int,
    default=100,
    help="Only process the first N links (> 0).",
)
parser.add_argument(
    "--force",
    action="store_true",
    help="Force check all links, ignoring cooldown/backoff (unsupported skipped)",
)


# ---- DB access --------------------------------------------------------------
def get_vendor_links(limit: int = 100, force: bool = False) -> list[dict[str, Any]]:
    """
    Pull vendor links from the database.

    When ``force`` is True all known links up to ``limit`` are returned
    (ignoring the usual due/backoff filtering) while unsupported vendors
    are skipped.  Otherwise only due links are returned.
    """
    if force:
        # Grab a plain list of links (no due/backoff filtering) and
        # filter to supported vendors only.
        res = supabase.table("cube_vendor_links").select("*").limit(limit).execute()
        data = res.data or []
        return [l for l in data if is_supported_vendor(l.get("url", ""))]
    # Default mode: server-side selection of due links with a per-vendor cap
    res = supabase.rpc(
        "due_vendor_links_capped", {"p_limit": limit, "p_per_vendor": 40}
    ).execute()
    return res.data or []


def update_vendor_link(
    link: Dict[str, Any],
    new_price: Optional[float],
    new_available: Optional[bool],
    reason: str,
    etag: Optional[str] = None,
    last_modified: Optional[str] = None,
) -> None:
    """
    Persist changes back to cube_vendor_links.
    We set updated_at here (UTC) so you don't depend on DB triggers.
    """
    old_price, old_av = link["price"], link["available"]
    logging.info(
        "5) UPDATE  | %-20s price: %s -> %s  available: %s -> %s  reason=%s",
        link["vendor_name"],
        old_price,
        new_price,
        old_av,
        new_available,
        reason,
    )

    updates = {
        "price": new_price,
        "available": new_available,
        "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        # Reset unchanged streak whenever we record a fresh update
        "streak_unchanged": 0,
    }
    if etag:
        updates["etag"] = etag
    if last_modified:
        updates["last_modified"] = last_modified
    supabase.table("cube_vendor_links").update(updates).eq("id", link["id"]).execute()


def update_vendor_metadata(
    row_id: int, *, etag: Optional[str] = None, last_modified: Optional[str] = None
) -> None:
    """Update cache headers and timestamp without touching price/availability/streak."""
    updates: Dict[str, Any] = {
        "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    if etag is not None:
        updates["etag"] = etag
    if last_modified is not None:
        updates["last_modified"] = last_modified
    supabase.table("cube_vendor_links").update(updates).eq("id", row_id).execute()


def streak_unchanged(
    row_id: int,
    current: Optional[int],
    etag: Optional[str] = None,
    last_modified: Optional[str] = None,
):
    # Increment unchanged streak when content hasn't changed (or 304)
    updates = {
        "streak_unchanged": (current or 0) + 1,
        "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    if etag:
        updates["etag"] = etag
    if last_modified:
        updates["last_modified"] = last_modified
    supabase.table("cube_vendor_links").update(updates).eq("id", row_id).execute()


# ---- HTTP fetch -------------------------------------------------------------
def _lower_headers(h: Dict[str, str]) -> Dict[str, str]:
    """Return a case-insensitive dict by lowercasing header names."""
    return {str(k).lower(): v for k, v in h.items()}


async def fetch_page_content(
    client: httpx.AsyncClient,
    url: str,
    *,
    etag: Optional[str] = None,
    last_modified: Optional[str] = None,
    debug: bool = False,
) -> Tuple[int, str, Dict[str, str], str]:
    """Fetch a product page with a polite UA and sensible timeout.

    Adds conditional headers if ETag or Last-Modified values are supplied.
    Returns a tuple of ``(status_code, html, headers, final_url)``.
    """
    headers = {
        "User-Agent": "CubeIndexBot/1.0 (+support@cubeindex.app)",
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
    }
    # Use conditional headers when available to allow 304 responses
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified
    resp = await client.get(url, headers=headers, timeout=12.0, follow_redirects=True)
    if debug:
        logging.debug(
            "   [HTTP] %s -> %s %s", url, resp.status_code, resp.reason_phrase
        )
        logging.debug("   [HTTP] Final URL: %s", resp.url)
        logging.debug("   [HTTP] Content-Type: %s", resp.headers.get("Content-Type"))
    # Normalize header keys to lowercase for case-insensitive access
    return resp.status_code, resp.text, _lower_headers(dict(resp.headers)), str(resp.url)


def respect_retry_after(headers: Dict[str, str]) -> float:
    """
    Parse Retry-After header; return seconds to wait (fallback 60s if bad date).
    """
    ra = headers.get("retry-after")
    if not ra:
        return 0.0
    try:
        return float(ra)
    except ValueError:
        # HTTP-date; try to parse and compute delta, else fallback
        try:
            dt_val = parsedate_to_datetime(ra)
            if not dt_val.tzinfo:
                dt_val = dt_val.replace(tzinfo=timezone.utc)
            delta = (dt_val - datetime.now(timezone.utc)).total_seconds()
            return max(0.0, float(delta))
        except Exception:
            return 60.0


# ---- JSON-LD extraction -----------------------------------------------------
def extract_json_ld_block(html: str, debug: bool = False) -> Optional[Dict[str, Any]]:
    """
    Return the first JSON-LD Product node (handles arrays & @graph) or None.
    """
    soup = BeautifulSoup(html, "lxml")
    blocks: list[Any] = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            text = tag.string or tag.get_text()
            if not text:
                continue
            blocks.append(json.loads(text))
        except Exception as e:
            if debug:
                logging.debug("   [JSON-LD] Failed to parse block: %r", e)
    if debug:
        logging.debug("   [JSON-LD] Found %d block(s).", len(blocks))

    def is_product(node: Dict[str, Any]) -> bool:
        t = node.get("@type")
        if isinstance(t, list):
            return any(str(x).lower() == "product" for x in t)
        return str(t).lower() == "product"

    # Flatten arrays and @graph forms
    candidates: list[Dict[str, Any]] = []
    for b in blocks:
        if isinstance(b, list):
            candidates.extend(b)  # type: ignore[index]
        elif isinstance(b, dict) and isinstance(b.get("@graph"), list):
            candidates.extend(b["@graph"])
        elif isinstance(b, dict):
            candidates.append(b)

    for node in candidates:
        if isinstance(node, dict) and is_product(node):
            if debug:
                logging.debug("   [JSON-LD] Using Product node.")
            return node

    if debug:
        logging.debug("   [JSON-LD] No Product node found.")
    return None


def extract_from_json_ld(
    product_node: Dict[str, Any], debug: bool = False
) -> Tuple[Optional[float], Optional[bool], Dict[str, Any]]:
    """
    Parse price & availability from a JSON-LD Product node.
    """
    offers = product_node.get("offers")
    if isinstance(offers, list):
        offers = offers[0] if offers else None

    price = None
    available = None

    if offers:
        price_raw = offers.get("price") or (offers.get("priceSpecification") or {}).get(
            "price"
        )
        availability_raw = str(offers.get("availability", "")).lower()

        if price_raw is not None:
            try:
                price = float(str(price_raw).replace(",", "."))
            except Exception as e:
                if debug:
                    logging.debug(
                        "   [JSON-LD] Price parse error: %r (raw=%r)", e, price_raw
                    )

        if "instock" in availability_raw:
            available = True
        elif "outofstock" in availability_raw or "soldout" in availability_raw:
            available = False
        elif "preorder" in availability_raw:
            available = True

        if debug:
            logging.debug(
                "   [JSON-LD] Extracted price=%s available=%s (raw=%s)",
                price,
                available,
                availability_raw,
            )

    return price, available, {"jsonld": product_node}


# ---- HTML fallback ----------------------------------------------------------
PRICE_RE = re.compile(
    r"(?:\$|€|£)?\s?(\d{1,5}(?:[.,]\d{2})?)\s?(?:€|eur|usd|gbp|£|\$)?", re.I
)
OOS_WORDS = ("out of stock", "sold out", "rupture", "épuisé")
INSTOCK_WORDS = ("in stock", "disponible", "ready to ship", "en stock")
PREORDER_WORDS = ("preorder", "précommande")


def _parse_vendor_specific(
    url: str, html: str
) -> Optional[Tuple[Optional[float], Optional[bool], Dict[str, Any]]]:
    """
    Call vendor-specific helpers when hostname matches.
    """
    host = urlparse(url).hostname or ""
    try:
        if host.endswith("thecubicle.com"):
            from src.price_tracking.helpers.thecubicle import parse_cubicle

            return parse_cubicle(html)
        if host.endswith("gancube.com"):
            from src.price_tracking.helpers.gancube import parse_gancube

            return parse_gancube(html)
        if host.endswith("speedcubeshop.com"):
            from src.price_tracking.helpers.scs import parse_scs

            return parse_scs(html)
        if host.endswith("speedcubes.co.za"):
            from src.price_tracking.helpers.speedcubes_co_za import (
                parse_speedcubes_co_za,
            )

            return parse_speedcubes_co_za(html)
    except Exception as e:
        logging.debug("   [HTML] Vendor helper failed: %r", e)
    return None


def extract_from_html(
    url: str, html: str, debug: bool = False
) -> Tuple[Optional[float], Optional[bool], Dict[str, Any]]:
    """
    Fallback: heuristics from raw HTML text and buttons.
    """
    # Prefer a vendor-specific parser first
    # Try dedicated vendor parser first (more reliable than heuristics)
    vs = _parse_vendor_specific(url, html)
    if vs:
        return vs

    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True).lower()
    text_ascii = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()

    available = None
    reason = "unknown"

    if any((w in text) or (w in text_ascii) for w in OOS_WORDS):
        available = False
        reason = "keyword:oos"
    elif any((w in text) or (w in text_ascii) for w in PREORDER_WORDS):
        available = True
        reason = "keyword:preorder"
    elif any((w in text) or (w in text_ascii) for w in INSTOCK_WORDS):
        available = True
        reason = "keyword:instock"
    else:
        # Look for common buy/add-to-cart cues in button-like elements
        for el in soup.find_all(["button", "a", "input"]):
            t = (el.get_text(" ", strip=True) or el.get("value") or "").strip()
            if not t:
                continue
            t_low = t.lower()
            t_ascii = unicodedata.normalize("NFKD", t_low).encode("ascii", "ignore").decode("ascii")
            if any(
                phrase in t_low or phrase in t_ascii
                for phrase in (
                    "add to cart",
                    "add to basket",
                    "add to bag",
                    "buy now",
                    "ajouter au panier",
                    "acheter",
                )
            ):
                available = True
                reason = "button:add-to-cart"
                break

    price = None
    match_text = None
    price_re = re.compile(
        r"(?:[$€£¥R]|usd|eur|gbp|zar)?\s*(\d{1,5}(?:[.,]\d{1,2})?)\s*(?:[$€£¥R]|usd|eur|gbp|zar)?",
        re.I,
    )
    m = price_re.search(text)
    if m:
        match_text = m.group(0)
        try:
            price = float(m.group(1).replace(",", "."))
        except Exception as e:
            if debug:
                logging.debug(
                    "   [HTML] Price regex parse error: %r (match=%r)", e, m.group(0)
                )

    if debug:
        logging.debug(
            "   [HTML] availability=%s (reason=%s) price=%s match=%r",
            available,
            reason,
            price,
            match_text,
        )

    return price, available, {"html": True, "reason": reason, "price_match": match_text}


# Override corrupted keyword constants (ensure robust matching)
OOS_WORDS = ("out of stock", "sold out", "rupture", "épuisé", "epuise")
PREORDER_WORDS = ("preorder", "précommande", "precommande")


# ---- Helpers ----------------------------------------------------------------
def decide_available(
    http_status: int, parsed_available: Optional[bool], debug: bool = False
) -> Tuple[Optional[bool], str]:
    """
    Merge HTTP signal with parsed availability.
    404/410 -> unavailable page, else prefer parsed value.
    """
    if http_status in (404, 410):
        if debug:
            logging.debug(
                "   [DECIDE] HTTP %s -> available=False (unavailable page)", http_status
            )
        return False, f"http:{http_status}"
    if parsed_available is not None:
        if debug:
            logging.debug("   [DECIDE] Parsed availability -> %s", parsed_available)
        return parsed_available, "parsed"
    if debug:
        logging.debug("   [DECIDE] availability unknown")
    return None, "unknown"


def ensure_debug_file(html: str, vendor: str, cube: str) -> str:
    """
    Save raw HTML for manual inspection when --save-html is set.
    Files are organized as .debug/<vendor>/<cube>.html
    """
    base = Path(".debug") / vendor
    base.mkdir(parents=True, exist_ok=True)
    out = base / f"{cube}.html"
    out.write_text(html, encoding="utf-8")
    return str(out)


def is_supported_vendor(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host.endswith(v) for v in SUPPORTED_VENDORS)


def vendor_host(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


async def throttle_for_vendor(url: str) -> None:
    """Enforce a minimum interval per vendor host, plus small jitter.

    A lock is used per vendor so different vendors can run in parallel while
    requests for the same vendor are serialized and respect ``VENDOR_MIN_INTERVAL``.
    """
    host = vendor_host(url)
    lock = vendor_locks[host]
    async with lock:
        min_gap = VENDOR_MIN_INTERVAL.get(host, DEFAULT_MIN_INTERVAL)
        now = time.monotonic()
        wait = (last_hit_at[host] + min_gap) - now
        if wait > 0:
            await asyncio.sleep(wait)
        await asyncio.sleep(random.uniform(*JITTER_RANGE))
        last_hit_at[host] = time.monotonic()


def recently_updated(link: dict[str, Any]) -> bool:
    """
    True if link.updated_at is within LINK_COOLDOWN.
    Expects ISO 8601 with Z or offset.
    """
    uat = link.get("updated_at")
    if not uat:
        return False
    try:
        ts = datetime.fromisoformat(str(uat).replace("Z", "+00:00"))
    except Exception:
        return False
    return datetime.now(timezone.utc) - ts < LINK_COOLDOWN


def effective_cooldown(streak: int) -> timedelta:
    # LINK_COOLDOWN * 2^streak, capped
    exp = max(0, min(streak, BACKOFF_EXP_CAP))
    cd = LINK_COOLDOWN * (2**exp)
    return cd if cd <= MAX_LINK_COOLDOWN else MAX_LINK_COOLDOWN


def td_hms(td: timedelta) -> str:
    secs = int(td.total_seconds())
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}h{m:02d}m{s:02d}s"


def backoff_status(link: dict[str, Any]) -> tuple[bool, timedelta, timedelta, int]:
    """
    Returns: (in_backoff, remaining, cooldown, streak)
    """
    uat = link.get("updated_at")
    streak = int(link.get("streak_unchanged") or 0)
    if not uat:
        return False, timedelta(0), LINK_COOLDOWN, streak
    try:
        ts = datetime.fromisoformat(str(uat).replace("Z", "+00:00"))
    except Exception:
        return False, timedelta(0), LINK_COOLDOWN, streak

    cooldown = effective_cooldown(streak)
    elapsed = datetime.now(timezone.utc) - ts
    remaining = cooldown - elapsed
    return (remaining > timedelta(0), max(remaining, timedelta(0)), cooldown, streak)


async def process_link(
    link: dict[str, Any],
    client: httpx.AsyncClient,
    progress: Progress,
    task_id: int,
    args: argparse.Namespace,
) -> tuple[list[dict[str, Any]], int, int, int, int]:
    """Process a single vendor link and return its outcome.

    Returns a tuple of ``(change_log, changed, unchanged, skipped, error)``.
    """
    vendor = link["vendor_name"]
    url = link["url"]
    cube_slug = link["cube_slug"]
    progress.update(task_id, description=f"[cyan]{vendor}[/] • {cube_slug}")

    change_log: list[dict[str, Any]] = []
    changed_count = 0
    unchanged_count = 0
    skipped_count = 0
    error_count = 0

    try:
        if not is_supported_vendor(url):
            skipped_count = 1
            logging.warning("0) SKIP    | Unsupported vendor for URL: %s", url)
            return (
                change_log,
                changed_count,
                unchanged_count,
                skipped_count,
                error_count,
            )

        in_backoff, remaining, cooldown, streak = backoff_status(link)
        if in_backoff and not args.force:
            skipped_count = 1
            logging.info(
                "0) SKIP    | Backoff active (streak=%s cooldown=%s remaining=%s)",
                streak,
                td_hms(cooldown),
                td_hms(remaining),
            )
            return (
                change_log,
                changed_count,
                unchanged_count,
                skipped_count,
                error_count,
            )

        await throttle_for_vendor(url)

        # 1) FETCH
        logging.info("1) FETCH   | requesting page...")
        try:
            status, html, headers, final_url = await fetch_page_content(
                client,
                url,
                etag=link.get("etag"),
                last_modified=link.get("last_modified"),
                debug=args.debug,
            )
        except Exception as e:
            error_count = 1
            logging.error("Fetch failed: %r", e)
            return (
                change_log,
                changed_count,
                unchanged_count,
                skipped_count,
                error_count,
            )
        logging.info("   FETCHED | HTTP=%s final_url=%s", status, final_url)

        if status == 304:
            logging.info("   NOTMOD | resource not modified; updating row anyway")
            # Treat as an update to refresh updated_at, cache headers and reset streak
            await asyncio.to_thread(
                update_vendor_link,
                link,
                link.get("price"),
                link.get("available"),
                "not-modified",
                headers.get("etag"),
                headers.get("last-modified"),
            )
            unchanged_count = 1
            return (
                change_log,
                changed_count,
                unchanged_count,
                skipped_count,
                error_count,
            )

        # Handle back-pressure (429 / 503) once
        if status in (429, 503):
            # Respect Retry-After when present; otherwise use a conservative wait
            wait_for = max(respect_retry_after(headers), 30.0)
            logging.warning("   BACKOFF | status=%s waiting %.1fs", status, wait_for)
            await asyncio.sleep(wait_for)
            await throttle_for_vendor(url)
            try:
                status, html, headers, final_url = await fetch_page_content(
                    client,
                    url,
                    etag=link.get("etag"),
                    last_modified=link.get("last_modified"),
                    debug=args.debug,
                )
            except Exception as e:
                error_count = 1
                logging.error("Retry fetch failed: %r", e)
                return (
                    change_log,
                    changed_count,
                    unchanged_count,
                    skipped_count,
                    error_count,
                )
            logging.info("   RETRIED | HTTP=%s final_url=%s", status, final_url)

            if status == 304:
                logging.info("   NOTMOD | resource not modified; updating row anyway")
                # Treat as an update to refresh updated_at, cache headers and reset streak
                await asyncio.to_thread(
                    update_vendor_link,
                    link,
                    link.get("price"),
                    link.get("available"),
                    "not-modified",
                    headers.get("etag"),
                    headers.get("last-modified"),
                )
                unchanged_count = 1
                return (
                    change_log,
                    changed_count,
                    unchanged_count,
                    skipped_count,
                    error_count,
                )

        etag_hdr = headers.get("etag")
        last_mod_hdr = headers.get("last-modified")

        if args.save_html:
            path = await asyncio.to_thread(ensure_debug_file, html, vendor, cube_slug)
            logging.info("   SAVED   | HTML -> %s", path)

        # 2) JSON-LD
        logging.info("2) JSON-LD | extracting structured data...")
        price, available, raw = None, None, {}
        product_node = extract_json_ld_block(html, debug=args.debug)
        if product_node:
            price, available, raw = extract_from_json_ld(product_node, debug=args.debug)
        logging.info("   JSON-LD | price=%s available=%s", price, available)

        # 3) HTML fallback
        if price is None or available is None:
            logging.info("3) HTML    | falling back to HTML heuristics...")
            p2, a2, raw2 = extract_from_html(final_url, html, debug=args.debug)
            if price is None:
                price = p2
            if available is None:
                available = a2
            raw.update(raw2)
        logging.info("   HTML    | price=%s available=%s", price, available)

        # 4) DECIDE availability
        logging.info("4) DECIDE  | merging HTTP + parse signals...")
        final_available, reason = decide_available(status, available, debug=args.debug)
        logging.info(
            "   DECIDE  | final_available=%s reason=%s", final_available, reason
        )

        # Compare vs DB row; don’t lose explicit False/0.00
        new_price = price if price is not None else link["price"]
        new_available = (
            final_available if final_available is not None else link["available"]
        )

        changed = (new_price != link["price"]) or (new_available != link["available"])
        logging.info(
            "   CHECK   | changed=%s (old_price=%s old_av=%s)",
            changed,
            link["price"],
            link["available"],
        )

        try:
            if changed:
                field_changes = []
                if new_price != link["price"]:
                    field_changes.append(("price", link["price"], new_price))
                if new_available != link["available"]:
                    field_changes.append(
                        ("available", link["available"], new_available)
                    )
                change_log.append(
                    {
                        "vendor_name": link["vendor_name"],
                        "cube_slug": link["cube_slug"],
                        "changes": field_changes,
                    }
                )
                await asyncio.to_thread(
                    update_vendor_link,
                    link,
                    new_price,
                    new_available,
                    reason,
                    etag_hdr,
                    last_mod_hdr,
                )
                changed_count = 1
            else:
                # Update row even when values are unchanged (refresh updated_at and reset streak)
                await asyncio.to_thread(
                    update_vendor_link,
                    link,
                    new_price,
                    new_available,
                    "unchanged",
                    etag_hdr,
                    last_mod_hdr,
                )
                logging.info("5) UPDATE  | values unchanged; row refreshed.")
                unchanged_count = 1
        except Exception as e:
            error_count = 1
            logging.error("DB update failed: %r", e)

        if args.debug:
            # Truncate raw signals to avoid huge logs
            logging.debug("RAW SIGNALS: %s", json.dumps(raw, ensure_ascii=False)[:2000])

        return (
            change_log,
            changed_count,
            unchanged_count,
            skipped_count,
            error_count,
        )
    finally:
        progress.advance(task_id)


# ---- Main -------------------------------------------------------------------
if __name__ == "__main__":
    args = parser.parse_args()

    # Configure logging:
    # - Default: logs OFF (except warnings/errors from libraries)
    # - --log  : INFO
    # - --debug: DEBUG
    log_level = logging.WARNING
    if args.log:
        log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG

    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )

    console.rule("[bold cyan]CubeIndex Price Tracker")
    console.print("Loading vendor links from database...")

    links = get_vendor_links(args.limit if args.limit > 0 else 100, force=args.force)

    if not links:
        console.print("[red]No vendor links found.[/]")
        sys.exit(1)

    total = len(links)
    console.print(f"[green]Found {total} link(s). Starting run...[/]")

    async def runner() -> list[tuple[list[dict[str, Any]], int, int, int, int]]:
        async with httpx.AsyncClient() as client:
            with Progress(
                TextColumn("[bold]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                transient=False,
                console=console,
            ) as progress:
                task = progress.add_task("Processing", total=total)
                sem = asyncio.Semaphore(WORKER_CONCURRENCY)

                async def sem_task(link: dict[str, Any]):
                    async with sem:
                        return await process_link(link, client, progress, task, args)

                return await asyncio.gather(*(sem_task(l) for l in links))

    results = asyncio.run(runner())

    change_log: list[dict[str, Any]] = []
    changed_count = 0
    unchanged_count = 0
    skipped_count = 0
    error_count = 0
    for clog, changed, unchanged, skipped, error in results:
        change_log.extend(clog)
        changed_count += changed
        unchanged_count += unchanged
        skipped_count += skipped
        error_count += error

    console.rule("[bold]Summary")
    console.print(
        f"[green]Changed:[/] {changed_count}  "
        f"[yellow]Unchanged:[/] {unchanged_count}  "
        f"[blue]Skipped:[/] {skipped_count}  "
        f"[red]Errors:[/]{error_count}"
    )
    if change_log:
        table = Table(title="Updated Fields")
        table.add_column("Vendor")
        table.add_column("Cube")
        table.add_column("Field")
        table.add_column("Old")
        table.add_column("New")
        for entry in change_log:
            vendor = entry["vendor_name"]
            cube = entry["cube_slug"]
            for field, old, new in entry["changes"]:
                table.add_row(vendor, cube, field, str(old), str(new))
        console.print(table)
