import sys
import os
import argparse
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Iterable
import datetime as dt

import requests
from bs4 import BeautifulSoup
import extruct
from w3lib.html import get_base_url
from urllib.parse import urlparse

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
from rich.logging import RichHandler

console = Console()

# ---- Supported vendors (hostname fragments) ----
SUPPORTED_VENDORS = [
    "thecubicle.com",
    "gancube.com",
    "speedcubeshop.com",
    "speedcubes.co.za",
]

# ---- CLI --------------------------------------------------------------------
parser = argparse.ArgumentParser(
    "fetch_cube_price",
    description="Fetch price & availability for known vendor links and update DB.",
)
# Logging is now optional:
parser.add_argument("--log", action="store_true", help="Enable pretty INFO logs.")
parser.add_argument("--debug", action="store_true", help="Enable DEBUG logs.")
parser.add_argument(
    "--save-html",
    action="store_true",
    help="Save fetched HTML to ./.debug/<vendor>/<cube>.html",
)
parser.add_argument(
    "--limit", type=int, default=0, help="Only process the first N links (0 = all)."
)


# ---- DB access --------------------------------------------------------------
def get_vendor_links() -> list[dict[str, Any]]:
    """
    Pull all vendor links (or a subset with --limit).
    We rely on: cube_vendor_links(id,url,vendor_name,cube_slug,price,available,updated_at)
    """
    res = (
        supabase.table("cube_vendor_links")
        .select("id,url,vendor_name,cube_slug,price,available,updated_at")
        .order("updated_at", desc=True)
        .execute()
    )
    return res.data or []


def update_vendor_link(
    link: Dict[str, Any],
    new_price: Optional[float],
    new_available: Optional[bool],
    reason: str,
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

    supabase.table("cube_vendor_links").update(
        {
            "price": new_price,
            "available": new_available,
            "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
    ).eq("id", link["id"]).execute()

    supabase.table("cube_vendor_links_snapshot").insert(
        {
            "price": new_price,
            "available": new_available,
            "vendor_name": link["vendor_name"],
            "cube_slug": link["cube_slug"],
            "url": link["url"],
        }
    ).execute()


# ---- HTTP fetch -------------------------------------------------------------
def fetch_page_content(
    url: str, debug: bool = False
) -> Tuple[int, str, Dict[str, str], str]:
    """
    Fetch a product page with a polite UA and sensible timeout.
    Returns: (status_code, html, headers, final_url)
    """
    headers = {
        "User-Agent": "CubeIndexBot/1.0 (+support@cubeindex.app)",
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
    }
    resp = requests.get(url, headers=headers, timeout=25, allow_redirects=True)
    if debug:
        logging.debug("   [HTTP] %s -> %s %s", url, resp.status_code, resp.reason)
        logging.debug("   [HTTP] Final URL: %s", resp.url)
        logging.debug("   [HTTP] Content-Type: %s", resp.headers.get("Content-Type"))
    return resp.status_code, resp.text, dict(resp.headers), resp.url


# ---- JSON-LD extraction -----------------------------------------------------
def extract_json_ld_block(
    html: str, url: str, debug: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Return the first JSON-LD Product node (handles arrays & @graph) or None.
    extruct extracts structured data like JSON-LD reliably.
    """
    data = extruct.extract(
        html, base_url=get_base_url(html, url), syntaxes=["json-ld"], uniform=True
    )
    blocks = data.get("json-ld", []) or []
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
    vs = _parse_vendor_specific(url, html)
    if vs:
        return vs

    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True).lower()

    available = None
    reason = "unknown"

    if any(w in text for w in OOS_WORDS):
        available = False
        reason = "keyword:oos"
    elif any(w in text for w in PREORDER_WORDS):
        available = True
        reason = "keyword:preorder"
    elif any(w in text for w in INSTOCK_WORDS):
        available = True
        reason = "keyword:instock"
    elif soup.select_one(
        'button:contains("Add to cart"),button:contains("Ajouter au panier")'
    ):
        available = True
        reason = "button:add-to-cart"

    price = None
    match_text = None
    m = PRICE_RE.search(text)
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
    """
    base = Path(".debug") / vendor
    base.mkdir(parents=True, exist_ok=True)
    out = base / f"{cube}.html"
    out.write_text(html, encoding="utf-8")
    return str(out)


def is_supported_vendor(url: str) -> bool:
    return any(v in url for v in SUPPORTED_VENDORS)


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

    links = get_vendor_links()
    if args.limit and args.limit > 0:
        links = links[: args.limit]

    if not links:
        console.print("[red]No vendor links found.[/]")
        sys.exit(1)

    total = len(links)
    console.print(f"[green]Found {total} link(s). Starting run...[/]")

    # Always-on progress bar
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

        changed_count = 0
        unchanged_count = 0
        skipped_count = 0
        error_count = 0

        for link in links:
            vendor = link["vendor_name"]
            url = link["url"]
            cube_slug = link["cube_slug"]
            progress.update(task, description=f"[cyan]{vendor}[/] • {cube_slug}")

            if not is_supported_vendor(url):
                skipped_count += 1
                logging.warning("0) SKIP    | Unsupported vendor for URL: %s", url)
                progress.advance(task)
                continue

            # 1) FETCH
            logging.info("1) FETCH   | requesting page...")
            try:
                status, html, headers, final_url = fetch_page_content(
                    url, debug=args.debug
                )
            except Exception as e:
                error_count += 1
                logging.error("Fetch failed: %r", e)
                progress.advance(task)
                continue
            logging.info("   FETCHED | HTTP=%s final_url=%s", status, final_url)

            if args.save_html:
                path = ensure_debug_file(html, vendor, cube_slug)
                logging.info("   SAVED   | HTML -> %s", path)

            # 2) JSON-LD
            logging.info("2) JSON-LD | extracting structured data...")
            price, available, raw = None, None, {}
            product_node = extract_json_ld_block(html, final_url, debug=args.debug)
            if product_node:
                price, available, raw = extract_from_json_ld(
                    product_node, debug=args.debug
                )
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
            final_available, reason = decide_available(
                status, available, debug=args.debug
            )
            logging.info(
                "   DECIDE  | final_available=%s reason=%s", final_available, reason
            )

            # Compare vs DB row; don’t lose explicit False/0.00
            new_price = price if price is not None else link["price"]
            new_available = (
                final_available if final_available is not None else link["available"]
            )

            changed = (new_price != link["price"]) or (
                new_available != link["available"]
            )
            logging.info(
                "   CHECK   | changed=%s (old_price=%s old_av=%s)",
                changed,
                link["price"],
                link["available"],
            )

            try:
                if changed:
                    update_vendor_link(link, new_price, new_available, reason)
                    changed_count += 1
                else:
                    logging.info("5) UPDATE  | no changes detected.")
                    unchanged_count += 1
            except Exception as e:
                error_count += 1
                logging.error("DB update failed: %r", e)

            if args.debug:
                # Truncate raw signals to avoid huge logs
                logging.debug(
                    "RAW SIGNALS: %s", json.dumps(raw, ensure_ascii=False)[:2000]
                )

            progress.advance(task)

    console.rule("[bold]Summary")
    console.print(
        f"[green]Changed:[/] {changed_count}  "
        f"[yellow]Unchanged:[/] {unchanged_count}  "
        f"[blue]Skipped:[/] {skipped_count}  "
        f"[red]Errors:[/]{error_count}"
    )
