import sys
import os
import argparse
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup
import extruct
from w3lib.html import get_base_url
from urllib.parse import urlparse

# allow "src.common.supabaseClient" import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.common.supabaseClient import supabase  # noqa: E402


SUPPORTED_VENDORS = [
    "thecubicle.com",
    "gancube.com",
    "speedcubeshop.com",
    "speedcubes.co.za",
]

# ----------------------------
# CLI
# ----------------------------
parser = argparse.ArgumentParser("fetch_cube_price")
parser.add_argument("--debug", action="store_true", help="Verbose debugging logs.")
parser.add_argument(
    "--save-html",
    action="store_true",
    help="Save fetched HTML to ./.debug/<vendor>/index.html",
)
parser.add_argument(
    "--limit", type=int, default=0, help="Only process the first N links (0 = all)."
)


# ----------------------------
# DB access
# ----------------------------
def get_vendor_links():
    """Return ALL vendor links for a cube (so you can see differences per store)."""
    res = (
        supabase.table("cube_vendor_links")
        .select("id,url,vendor_name,cube_slug,price,available,updated_at")
        .execute()
    )
    return res.data or []


def update_vendor_link(
    link: Dict[str, Any],
    new_price: float,
    new_available: bool,
):
    """Return ALL vendor links for a cube (so you can see differences per store)."""

    # Summary print (kept like your original)
    print(f"Cube: {link['cube_slug']}")
    print(f"Vendor: {link["vendor_name"]}")
    print(f"Price: {link["price"]} -> {new_price}".strip())
    print(f"Available: {link["available"]} -> {new_available} (reason={reason})")

    supabase.table("cube_vendor_links").update(
        {"price": new_price, "available": new_available, "updated_at": "now()"}
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


# ----------------------------
# HTTP fetch
# ----------------------------
def fetch_page_content(
    url: str, debug: bool = False
) -> Tuple[int, str, Dict[str, str], str]:
    headers = {
        "User-Agent": "CubeIndexBot/1.0 (+support@cubeindex.app)",
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
    }
    resp = requests.get(url, headers=headers, timeout=25, allow_redirects=True)
    if debug:
        logging.debug(f"[HTTP] GET {url} -> {resp.status_code} {resp.reason}")
        logging.debug(f"[HTTP] Final URL: {resp.url}")
        logging.debug(f"[HTTP] Content-Type: {resp.headers.get('Content-Type')}")
    return resp.status_code, resp.text, dict(resp.headers), resp.url


# ----------------------------
# JSON-LD extraction
# ----------------------------
def extract_json_ld_block(
    html: str, url: str, debug: bool = False
) -> Optional[Dict[str, Any]]:
    """Return the first Product node (handles arrays & @graph) or None."""
    data = extruct.extract(
        html, base_url=get_base_url(html, url), syntaxes=["json-ld"], uniform=True
    )
    blocks = data.get("json-ld", []) or []
    if debug:
        logging.debug(f"[JSON-LD] Found {len(blocks)} json-ld block(s).")

    def is_product(node: Dict[str, Any]) -> bool:
        t = node.get("@type")
        if isinstance(t, list):
            return any(str(x).lower() == "product" for x in t)
        return str(t).lower() == "product"

    # flatten arrays and @graph
    candidates = []
    for b in blocks:
        if isinstance(b, list):
            candidates.extend(b)
        elif isinstance(b, dict) and "@graph" in b and isinstance(b["@graph"], list):
            candidates.extend(b["@graph"])
        elif isinstance(b, dict):
            candidates.append(b)

    for node in candidates:
        if isinstance(node, dict) and is_product(node):
            if debug:
                logging.debug("[JSON-LD] Using Product node from JSON-LD.")
            return node

    if debug:
        logging.debug("[JSON-LD] No Product node found.")
    return None


def extract_from_json_ld(
    product_node: Dict[str, Any], debug: bool = False
) -> Tuple[Optional[float], Optional[bool], Dict[str, Any]]:
    """Extract price, availability from a JSON-LD Product node."""
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
                        f"[JSON-LD] Price parse error: {e!r} (raw={price_raw})"
                    )

        if "instock" in availability_raw:
            available = True
        elif "outofstock" in availability_raw or "soldout" in availability_raw:
            available = False
        elif "preorder" in availability_raw:
            # you may want to treat preorder as available=True
            available = True

        if debug:
            logging.debug(
                f"[JSON-LD] Extracted price={price}, available={available}, availability_raw={availability_raw}"
            )

    return price, available, {"jsonld": product_node}


# ----------------------------
# HTML fallback
# ----------------------------
PRICE_RE = re.compile(
    r"(?:\$|€|£)?\s?(\d{1,5}(?:[.,]\d{2})?)\s?(?:€|eur|usd|gbp|£|\$)?", re.I
)
OOS_WORDS = ("out of stock", "sold out", "rupture", "épuisé")
INSTOCK_WORDS = ("in stock", "disponible", "ready to ship", "en stock")
PREORDER_WORDS = ("preorder", "précommande")


def extract_from_html(
    url: str, html: str, debug: bool = False
) -> Tuple[Optional[float], Optional[bool], Dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True).lower()
    available = None
    reason = "unknown"
    hostname = urlparse(url).hostname

    if hostname == "www.thecubicle.com":
        from src.price_tracking.helpers.thecubicle import parse_cubicle

        return parse_cubicle(html)
    elif hostname == "www.gancube.com":
        from src.price_tracking.helpers.gancube import parse_gancube

        return parse_gancube(html)
    elif hostname == "www.speedcubeshop.com":
        from src.price_tracking.helpers.scs import parse_scs

        return parse_scs(html)
    elif hostname == "www.speedcubes.co.za":
        from src.price_tracking.helpers.speedcubes_co_za import parse_speedcubes_co_za

        return parse_speedcubes_co_za(html)
    else:
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
        m = PRICE_RE.search(text)
        match_text = None
        if m:
            match_text = m.group(0)
            try:
                price = float(m.group(1).replace(",", "."))
            except Exception as e:
                if debug:
                    logging.debug(
                        f"[HTML] Price regex parse error: {e!r} (match={m.group(0)!r})"
                    )

        if debug:
            logging.debug(
                f"[HTML] availability={available} (reason={reason}), price={price}, price_match={match_text!r}"
            )

        return (
            price,
            available,
            {"html": True, "reason": reason, "price_match": match_text},
        )


# ----------------------------
# Helpers
# ----------------------------
def decide_available(
    http_status: int, parsed_available: Optional[bool], debug: bool = False
) -> Tuple[Optional[bool], str]:
    """Turn HTTP + parsed signal into final availability flag and reason."""
    if http_status in (404, 410):
        if debug:
            logging.debug(
                f"[DECIDE] HTTP {http_status} -> available=False (unavailable page)"
            )
        return False, f"http:{http_status}"
    if parsed_available is not None:
        if debug:
            logging.debug(f"[DECIDE] Parsed availability -> {parsed_available}")
        return parsed_available, "parsed"
    if debug:
        logging.debug("[DECIDE] availability unknown")
    return None, "unknown"


def ensure_debug_file(html: str, vendor: str, cube: str):
    base = Path(".debug") / vendor
    base.mkdir(parents=True, exist_ok=True)
    out = base / f"{cube}-index.html"
    out.write_text(html, encoding="utf-8")
    return str(out)


def is_supported_vendor(url: str) -> bool:
    return any(vendor in url for vendor in SUPPORTED_VENDORS)


# ----------------------------
# Main
# ----------------------------
if __name__ == "__main__":
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    links = get_vendor_links()
    if args.limit and args.limit > 0:
        links = links[: args.limit]

    if not links:
        logging.error("No vendor links found")
        sys.exit(1)

    for link in links:
        vendor = link["vendor_name"]
        url = link["url"]
        logging.info("=== %s | %s ===", vendor, url)

        if not is_supported_vendor(url):
            logging.error("Unsupported vendor: %s", vendor)
            continue

        try:
            status, html, headers, final_url = fetch_page_content(url, debug=args.debug)
        except Exception as e:
            logging.error("Fetch failed: %r", e)
            continue

        if args.save_html:
            path = ensure_debug_file(html, vendor, link["cube_slug"])
            logging.info("Saved HTML to %s", path)

        # 1) JSON-LD first
        price, available, raw = None, None, {}

        product_node = extract_json_ld_block(html, final_url, debug=args.debug)
        if product_node:
            price, available, raw = extract_from_json_ld(
                product_node, debug=args.debug
            )

        # 2) Fallback to HTML
        if price is None or available is None:
            p2, a2, raw2 = extract_from_html(url, html, debug=args.debug)
            if price is None:
                price = p2
            if available is None:
                available = a2
            raw.update(raw2)

        # 3) Decide final availability with HTTP status
        final_available, reason = decide_available(status, available, debug=args.debug)

        print(f"HTTP: {status}")
        if price != link["price"] or final_available != link["available"]:
            update_vendor_link(
                link,
                price or link["price"],
                final_available or link["available"],
            )
        else:
            logging.info("No change")

        # Extra debug dump (opt-in)
        if args.debug:
            logging.debug("Raw signals: %s", json.dumps(raw, ensure_ascii=False)[:2000])
