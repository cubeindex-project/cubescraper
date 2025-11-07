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

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Literal, Optional, Tuple
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

# Allow "src.common.supabaseClient" import regardless of entrypoint.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.common.supabaseClient import supabase


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

SUPPORTED_VENDORS = (
    "thecubicle.com",
    "gancube.com",
    "speedcubes.co.za",
)

VENDOR_PARSERS: Dict[str, str] = {
    "thecubicle.com": "src.price_tracking.helpers.thecubicle:parse_cubicle",
    "gancube.com": "src.price_tracking.helpers.gancube:parse_gancube",
    "speedcubeshop.com": "src.price_tracking.helpers.scs:parse_scs",
    "speedcubes.co.za": "src.price_tracking.helpers.speedcubes_co_za:parse_speedcubes_co_za",
}

REQUEST_TIMEOUT = 15.0
COOLDOWN = timedelta(hours=12)

DEFAULT_HEADERS = {
    "User-Agent": "CubeIndexBot/1.0 (+support@cubeindex.app)",
    "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
}

PRICE_RE = re.compile(
    r"(?:[$\u20ac\u00a3]|usd|eur|gbp|zar)?\s*(\d{1,5}(?:[.,]\d{1,2})?)",
    re.IGNORECASE,
)
OOS_KEYWORDS = ("out of stock", "sold out", "rupture", "epuise")
INSTOCK_KEYWORDS = ("in stock", "ready to ship", "en stock", "disponible")
PREORDER_KEYWORDS = ("preorder", "pre-order", "precommande")


# -----------------------------------------------------------------------------
# Dataclasses
# -----------------------------------------------------------------------------

@dataclass(slots=True)
class ProcessOptions:
    """Runtime flags that influence how a link is processed."""
    force: bool = False
    save_html: bool = False


@dataclass(slots=True)
class ParsedSignals:
    """Intermediate container for parsed price and availability signals."""
    price: Optional[float]
    available: Optional[bool]


@dataclass(slots=True)
class ProcessLinkUpdate:
    """Captured changes that should be flushed back to the database."""
    row_id: int
    price: Optional[float]
    available: Optional[bool]
    etag: Optional[str]
    last_modified: Optional[str]
    streak: int


@dataclass(slots=True)
class ProcessLinkResult:
    """Return value from ``process_link`` describing outcome and pending update."""
    outcome: Literal["changed", "unchanged", "skipped", "error"]
    price: Optional[float]
    available: Optional[bool]
    status_code: Optional[int] = None
    update: Optional[ProcessLinkUpdate] = None


# -----------------------------------------------------------------------------
# CLI parsing
# -----------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    """Build and return the CLI argument parser for the module entrypoint."""
    parser = argparse.ArgumentParser(
        "fetch_cube_price",
        description="Fetch price & availability for known vendor links and update DB.",
    )
    parser.add_argument("--limit", type=int, default=100, help="Process at most N links.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore the cooldown window and reprocess all supported links.",
    )
    parser.add_argument(
        "--save-html",
        action="store_true",
        help="Persist fetched HTML under ./.debug/<vendor>/<cube>.html",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Verbose log output (DEBUG level).",
    )
    return parser.parse_args()


# -----------------------------------------------------------------------------
# Database helpers
# -----------------------------------------------------------------------------

def fetch_all_links(limit: int) -> List[Dict[str, Any]]:
    """Return the first ``limit`` vendor link rows regardless of cooldown/backoff."""
    resp = supabase.table("cube_vendor_links").select("*").limit(limit).execute()
    return resp.data or []


def fetch_due_links(limit: int) -> List[Dict[str, Any]]:
    """Return vendor links flagged as due via the ``due_vendor_links_capped`` RPC."""
    resp = supabase.rpc(
        "due_vendor_links_capped", {"p_limit": limit, "p_per_vendor": 40}
    ).execute()
    return resp.data or []


def filter_supported_links(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter out any link whose host is not recognised in ``SUPPORTED_VENDORS``."""
    return [row for row in rows if is_supported_vendor(row.get("url", ""))]


def load_vendor_links(limit: int, force: bool) -> List[Dict[str, Any]]:
    """Load raw link rows from Supabase honouring ``force`` and supported host filter."""
    rows = fetch_all_links(limit) if force else fetch_due_links(limit)
    return filter_supported_links(rows)


def recently_updated(link: Dict[str, Any]) -> bool:
    """True when the link was refreshed within the configured cooldown window."""
    updated_at = link.get("updated_at")
    if not updated_at:
        return False
    try:
        ts = datetime.fromisoformat(str(updated_at).replace("Z", "+00:00"))
    except ValueError:
        return False
    return datetime.now(timezone.utc) - ts < COOLDOWN


# -----------------------------------------------------------------------------
# Networking helpers
# -----------------------------------------------------------------------------

def vendor_host(url: str) -> str:
    """Extract and lowercase the hostname portion of a vendor URL."""
    return (urlparse(url).hostname or "").lower()


def is_supported_vendor(url: str) -> bool:
    """Check whether the URL belongs to one of the known vendor domains."""
    host = vendor_host(url)
    return any(host.endswith(domain) for domain in SUPPORTED_VENDORS)


def resolve_vendor_parser(url: str) -> Optional[Callable[[str], Any]]:
    """Dynamically import a vendor-specific parser based on the URL host."""
    host = vendor_host(url)
    for domain, dotted in VENDOR_PARSERS.items():
        if host.endswith(domain):
            module_name, func_name = dotted.split(":")
            module = __import__(module_name, fromlist=[func_name])
            return getattr(module, func_name)
    return None


def build_request_headers(etag: Optional[str], last_modified: Optional[str]) -> Dict[str, str]:
    """Prepare conditional request headers using cached ETag/Last-Modified values."""
    headers = dict(DEFAULT_HEADERS)
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified
    return headers


def fetch_product_response(
    client: httpx.Client,
    url: str,
    *,
    etag: Optional[str],
    last_modified: Optional[str],
) -> httpx.Response:
    """Execute a GET request for the product URL with polite headers and timeout."""
    headers = build_request_headers(etag, last_modified)
    return client.get(url, headers=headers)


def extract_cache_headers(response: httpx.Response) -> Tuple[Optional[str], Optional[str]]:
    """Pull out ETag and Last-Modified headers from a response for persistence."""
    return response.headers.get("etag"), response.headers.get("last-modified")


# -----------------------------------------------------------------------------
# Parsing helpers
# -----------------------------------------------------------------------------

def iter_jsonld_nodes(payload: Any) -> Iterable[Any]:
    """Yield each element inside JSON-LD structures, normalising lists/@graph."""
    if isinstance(payload, list):
        for item in payload:
            yield from iter_jsonld_nodes(item)
    elif isinstance(payload, dict) and isinstance(payload.get("@graph"), list):
        for item in payload["@graph"]:
            yield from iter_jsonld_nodes(item)
    else:
        yield payload


def extract_json_ld(html: str) -> Optional[Dict[str, Any]]:
    """Return the first JSON-LD product node found within the page or None."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all("script", type="application/ld+json"):
        text = tag.string or tag.get_text()
        if not text:
            continue
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            continue
        for node in iter_jsonld_nodes(data):
            if isinstance(node, dict):
                type_field = node.get("@type")
                types = type_field if isinstance(type_field, list) else [type_field]
                if any(str(t).lower() == "product" for t in types if t):
                    return node
    return None


def parse_jsonld_signals(html: str) -> ParsedSignals:
    """Parse price and availability from JSON-LD Product data, when present."""
    node = extract_json_ld(html)
    if not node:
        return ParsedSignals(None, None)

    offers = node.get("offers")
    if isinstance(offers, list):
        offers = offers[0] if offers else None
    if not isinstance(offers, dict):
        return ParsedSignals(None, None)

    price_raw = offers.get("price")
    if price_raw is None and isinstance(offers.get("priceSpecification"), dict):
        price_raw = offers["priceSpecification"].get("price")

    price: Optional[float] = None
    if price_raw is not None:
        try:
            price = float(str(price_raw).replace(",", "."))
        except ValueError:
            price = None

    availability = None
    availability_raw = str(offers.get("availability", "")).lower()
    if "instock" in availability_raw or "in_stock" in availability_raw:
        availability = True
    elif "outofstock" in availability_raw or "soldout" in availability_raw:
        availability = False
    elif "preorder" in availability_raw:
        availability = True

    return ParsedSignals(price, availability)


def parse_vendor_signals(url: str, html: str) -> ParsedSignals:
    """Delegate to vendor-specific helpers for richer parsing when available."""
    parser = resolve_vendor_parser(url)
    if not parser:
        return ParsedSignals(None, None)
    try:
        result = parser(html)
    except Exception as exc:  # pragma: no cover - vendor helpers may fail unexpectedly
        logging.debug("Vendor parser failure for %s: %s", vendor_host(url), exc)
        return ParsedSignals(None, None)
    if isinstance(result, tuple) and len(result) >= 2:
        return ParsedSignals(result[0], result[1])
    return ParsedSignals(None, None)


def extract_plain_text(html: str) -> Tuple[str, str]:
    """Produce both raw and ASCII-normalised page text for keyword searches."""
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True).lower()
    ascii_text = (
        unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    )
    return text, ascii_text


def detect_availability_in_text(text: str, ascii_text: str) -> Optional[bool]:
    """Infer availability using simple keyword heuristics in the page text."""
    if any(word in ascii_text for word in OOS_KEYWORDS):
        return False
    if any(word in ascii_text for word in PREORDER_KEYWORDS):
        return True
    if any(word in ascii_text for word in INSTOCK_KEYWORDS):
        return True
    return None


def detect_price_in_text(text: str, ascii_text: str) -> Optional[float]:
    """Extract a numeric price candidate from the page text using regex."""
    for corpus in (text, ascii_text):
        match = PRICE_RE.search(corpus)
        if not match:
            continue
        try:
            return float(match.group(1).replace(",", "."))
        except ValueError:
            continue
    return None


def parse_text_signals(html: str) -> ParsedSignals:
    """Fallback parser combining text-based price and availability heuristics."""
    text, ascii_text = extract_plain_text(html)
    price = detect_price_in_text(text, ascii_text)
    available = detect_availability_in_text(text, ascii_text)
    return ParsedSignals(price, available)


def merge_signals(primary: ParsedSignals, secondary: ParsedSignals) -> ParsedSignals:
    """Overlay two signal sets, favouring already-populated values in ``primary``."""
    price = primary.price if primary.price is not None else secondary.price
    available = primary.available if primary.available is not None else secondary.available
    return ParsedSignals(price, available)


def collect_parsing_signals(url: str, html: str) -> ParsedSignals:
    """Run parsers in order of fidelity and merge their outputs into one result."""
    signals = ParsedSignals(None, None)
    signals = merge_signals(signals, parse_jsonld_signals(html))
    if signals.price is None or signals.available is None:
        signals = merge_signals(signals, parse_vendor_signals(url, html))
    if signals.price is None or signals.available is None:
        signals = merge_signals(signals, parse_text_signals(html))
    return signals


# -----------------------------------------------------------------------------
# Persistence helpers
# -----------------------------------------------------------------------------

def decide_available(status_code: int, parsed_available: Optional[bool]) -> Optional[bool]:
    """Combine HTTP status with parsed signals to infer final availability."""
    if status_code in (404, 410):
        return False
    return parsed_available


def write_debug_html(html: str, vendor: str, cube: str) -> str:
    """Persist the raw HTML to disk for debugging when ``--save-html`` is set."""
    base = Path(".debug") / vendor
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{cube}.html"
    path.write_text(html, encoding="utf-8")
    return str(path)


def calculate_streak(link: Dict[str, Any], changed: bool) -> int:
    """Increment or reset the unchanged streak depending on whether values changed."""
    current = int(link.get("streak_unchanged") or 0)
    return 0 if changed else current + 1


def coalesce_value(parsed: Optional[Any], existing: Optional[Any]) -> Optional[Any]:
    """Prefer the parsed value unless it is ``None``."""
    return parsed if parsed is not None else existing


def create_update(
    link_id: int,
    price: Optional[float],
    available: Optional[bool],
    etag: Optional[str],
    last_modified: Optional[str],
    streak: int,
) -> ProcessLinkUpdate:
    """Package the new values and cache headers for persistence."""
    return ProcessLinkUpdate(
        row_id=link_id,
        price=price,
        available=available,
        etag=etag,
        last_modified=last_modified,
        streak=streak,
    )


def create_result(
    outcome: Literal["changed", "unchanged", "skipped", "error"],
    price: Optional[float],
    available: Optional[bool],
    status_code: Optional[int],
    update: Optional[ProcessLinkUpdate],
) -> ProcessLinkResult:
    """Helper constructor for the ``ProcessLinkResult`` dataclass."""
    return ProcessLinkResult(outcome, price, available, status_code, update)


def create_skip_result(link: Dict[str, Any]) -> ProcessLinkResult:
    """Return a skip result retaining the existing price/availability values."""
    return create_result("skipped", link.get("price"), link.get("available"), None, None)


def create_error_result(link: Dict[str, Any]) -> ProcessLinkResult:
    """Return an error result keeping the pre-existing values untouched."""
    return create_result("error", link.get("price"), link.get("available"), None, None)


def create_not_modified_update(
    link: Dict[str, Any],
    etag: Optional[str],
    last_modified: Optional[str],
) -> ProcessLinkUpdate:
    """Build an update payload for 304 responses that only adjust metadata."""
    streak = calculate_streak(link, changed=False)
    return create_update(
        link["id"],
        link.get("price"),
        link.get("available"),
        etag,
        last_modified,
        streak,
    )


def create_not_modified_result(
    link: Dict[str, Any],
    status_code: int,
    etag: Optional[str],
    last_modified: Optional[str],
) -> ProcessLinkResult:
    """Return a result for 304 responses so the caller updates metadata."""
    update = create_not_modified_update(link, etag, last_modified)
    return create_result(
        "unchanged", link.get("price"), link.get("available"), status_code, update
    )


def should_skip_vendor(link: Dict[str, Any]) -> bool:
    """True when the link host is not in the supported vendor list."""
    return not is_supported_vendor(link["url"])


def should_skip_cooldown(link: Dict[str, Any], force: bool) -> bool:
    """True when the link was processed recently and ``force`` is not enabled."""
    return (not force) and recently_updated(link)


def log_skip_reason(vendor: str, reason: str, url: str) -> None:
    """Emit a debug log explaining why a link was skipped."""
    logging.debug("[%s] %s -> skip (%s)", vendor, url, reason)


def log_fetch_failure(vendor: str, url: str, exc: Exception) -> None:
    """Log request exceptions so that transient issues are visible."""
    logging.error("[%s] %s -> request failed: %s", vendor, url, exc)


def log_fetch_status(vendor: str, url: str, status_code: int) -> None:
    """Log successful HTTP responses for traceability."""
    logging.info("[%s] %s -> HTTP %s", vendor, url, status_code)


def log_change(
    vendor: str,
    old_price: Optional[float],
    new_price: Optional[float],
    old_available: Optional[bool],
    new_available: Optional[bool],
) -> None:
    """Log the before/after values when a price or availability changes."""
    logging.debug(
        "[%s] price:%s -> %s, available:%s -> %s",
        vendor,
        old_price,
        new_price,
        old_available,
        new_available,
    )


def apply_update(update: ProcessLinkUpdate) -> None:
    """Persist the staged update back to Supabase."""
    payload: Dict[str, Any] = {
        "price": update.price,
        "available": update.available,
        "streak_unchanged": update.streak,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if update.etag is not None:
        payload["etag"] = update.etag
    if update.last_modified is not None:
        payload["last_modified"] = update.last_modified
    supabase.table("cube_vendor_links").update(payload).eq("id", update.row_id).execute()


# -----------------------------------------------------------------------------
# Processing logic
# -----------------------------------------------------------------------------

def process_link_with_session(
    link: Dict[str, Any],
    client: httpx.Client,
    options: ProcessOptions,
) -> ProcessLinkResult:
    """Process a single vendor link using an existing HTTP client session."""
    url = link["url"]
    vendor = link["vendor_name"]

    if should_skip_vendor(link):
        log_skip_reason(vendor, "unsupported vendor", url)
        return create_skip_result(link)

    if should_skip_cooldown(link, options.force):
        log_skip_reason(vendor, "cooldown active", url)
        return create_skip_result(link)

    try:
        response = fetch_product_response(
            client,
            url,
            etag=link.get("etag"),
            last_modified=link.get("last_modified"),
        )
    except Exception as exc:  # pragma: no cover - network errors depend on env
        log_fetch_failure(vendor, url, exc)
        return create_error_result(link)

    log_fetch_status(vendor, url, response.status_code)
    etag, last_modified = extract_cache_headers(response)

    if response.status_code == 304:
        return create_not_modified_result(link, response.status_code, etag, last_modified)

    html = response.text
    if options.save_html:
        path = write_debug_html(html, vendor, link["cube_slug"])
        logging.debug("[%s] HTML saved to %s", vendor, path)

    signals = collect_parsing_signals(url, html)
    final_available = decide_available(response.status_code, signals.available)

    old_price = link.get("price")
    old_available = link.get("available")
    new_price = coalesce_value(signals.price, old_price)
    new_available = coalesce_value(final_available, old_available)

    changed = (new_price != old_price) or (new_available != old_available)
    streak = calculate_streak(link, changed)
    update = create_update(link["id"], new_price, new_available, etag, last_modified, streak)

    log_change(vendor, old_price, new_price, old_available, new_available)

    outcome: Literal["changed", "unchanged"] = "changed" if changed else "unchanged"
    return create_result(outcome, new_price, new_available, response.status_code, update)


def process_link(
    link: Any,
    *,
    client: Optional[httpx.Client] = None,
    force: bool = False,
    debug: bool = False,  # Kept for CLI parity; logging level handles verbosity.
    save_html: bool = False,
) -> ProcessLinkResult:
    """Process a link dict (or raw URL) and return the parsed outcome."""
    options = ProcessOptions(force=force, save_html=save_html)
    owns_client = client is None
    session = client or httpx.Client(timeout=REQUEST_TIMEOUT, follow_redirects=True)
    link_dict = link
    suppress_update = False
    if isinstance(link, str):
        # Allow lightweight callers to supply a bare URL; fabricate the minimal row
        # structure expected by the rest of the pipeline and avoid DB updates.
        host = vendor_host(link)
        link_dict = {
            "id": None,
            "url": link,
            "vendor_name": host or "",
            "cube_slug": host or "",
            "price": None,
            "available": None,
            "etag": None,
            "last_modified": None,
            "streak_unchanged": 0,
            "updated_at": None,
        }
        suppress_update = True
    try:
        result = process_link_with_session(link_dict, session, options)
        if suppress_update:
            result.update = None
        return result
    finally:
        if owns_client:
            session.close()


def persist_process_result(result: ProcessLinkResult) -> None:
    """Apply the database update contained in a ``ProcessLinkResult``."""
    if result.update is None:
        return
    apply_update(result.update)


# -----------------------------------------------------------------------------
# CLI runner
# -----------------------------------------------------------------------------

def run(args: argparse.Namespace) -> Dict[str, int]:
    """Entry point for the CLI: iterate through links and collect stats."""
    links = load_vendor_links(args.limit, args.force)
    stats = {"changed": 0, "unchanged": 0, "skipped": 0, "errors": 0}
    if not links:
        logging.info("No vendor links to process.")
        return stats

    with httpx.Client(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
        for link in links:
            result = process_link(
                link,
                client=client,
                force=args.force,
                debug=args.debug,
                save_html=args.save_html,
            )
            persist_process_result(result)
            if result.outcome == "error":
                stats["errors"] += 1
            elif result.outcome in stats:
                stats[result.outcome] += 1

    return stats


def main() -> None:
    """CLI bootstrap that configures logging and kicks off processing."""
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(message)s",
    )

    logging.info("Loading vendor links (limit=%s, force=%s)...", args.limit, args.force)
    stats = run(args)
    logging.info(
        "Done. Changed=%s  Unchanged=%s  Skipped=%s  Errors=%s",
        stats["changed"],
        stats["unchanged"],
        stats["skipped"],
        stats["errors"],
    )


if __name__ == "__main__":
    main()
