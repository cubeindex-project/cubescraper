# fetch_cube_price.py
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
parser.add_argument("--debug", action="store_true", help="Verbose debugging logs.")
parser.add_argument(
    "--progress", action="store_true", help="Show a progress bar (tqdm)."
)
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
    extruct extracts structured data like JSON-LD reliably.  :contentReference[oaicite:3]{index=3}
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
            # Treat preorder as available if you want carts enabled
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
# BeautifulSoup (with SoupSieve) supports robust CSS selection and text queries. :contentReference[oaicite:4]{index=4}
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


def _maybe_wrap_progress(it: Iterable[dict[str, Any]], enabled: bool):
    """
    Optionally wrap an iterable with tqdm progress; fall back gracefully.
    """
    if not enabled:
        return it
    try:
        from tqdm import tqdm  # type: ignore

        return tqdm(it, unit="link")
    except Exception:
        logging.warning("tqdm not installed; continuing without progress bar.")
        return it


# ---- Main -------------------------------------------------------------------
if __name__ == "__main__":
    args = parser.parse_args()

    # Configure logging: INFO by default; DEBUG with --debug
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(levelname)s %(message)s",
    )
    logging.info("== CubeIndex Price Tracker ==")
    logging.info("Loading vendor links from database...")

    links = get_vendor_links()
    if args.limit and args.limit > 0:
        links = links[: args.limit]

    if not links:
        logging.error("No vendor links found.")
        sys.exit(1)

    logging.info("Found %d links. Starting run.", len(links))

    for link in _maybe_wrap_progress(links, args.progress):
        vendor = link["vendor_name"]
        url = link["url"]
        logging.info("→ %s | %s", vendor, url)

        if not is_supported_vendor(url):
            logging.warning("0) SKIP    | Unsupported vendor for URL: %s", url)
            continue

        # 1) FETCH
        logging.info("1) FETCH   | requesting page...")
        try:
            status, html, headers, final_url = fetch_page_content(url, debug=args.debug)
        except Exception as e:
            logging.error("Fetch failed: %r", e)
            continue
        logging.info("   FETCHED | HTTP=%s final_url=%s", status, final_url)

        if args.save_html:
            path = ensure_debug_file(html, vendor, link["cube_slug"])
            logging.info("   SAVED   | HTML -> %s", path)

        # 2) JSON-LD
        logging.info("2) JSON-LD | extracting structured data...")
        price, available, raw = None, None, {}
        product_node = extract_json_ld_block(html, final_url, debug=args.debug)
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

        if changed:
            update_vendor_link(link, new_price, new_available, reason)
        else:
            logging.info("5) UPDATE  | no changes detected.")

        if args.debug:
            # Truncate raw signals to avoid huge logs
            logging.debug("RAW SIGNALS: %s", json.dumps(raw, ensure_ascii=False)[:2000])

    logging.info("Run complete.")
