import sys
import time
import itertools
import json
import pathlib
import threading
import argparse
from typing import List, Dict, Any

import requests

# ---------------------------------------------------------------------------
# Store registry ------------------------------------------------------------
# ---------------------------------------------------------------------------
# Map a short, user‑friendly name to the public products.json endpoint.
# Add more stores here as you discover them.
STORES: Dict[str, str] = {
    "scs": "https://speedcubeshop.com/products.json",
    "cubicle": "https://thecubicle.com/products.json",
    "cubelelo": "https://cubelelo.com/products.json",
    "dailypuzzles": "https://dailypuzzles.com.au/products.json",
    "gancube": "https://gancube.com/products.json",
    "kewbz": "https://kewbz.co.uk/products.json",
    "sc-za": "https://www.speedcubes.co.za/products.json",
}

PAGE_LIMIT = 250  # Shopify max per page
SLEEP = 0.7  # politeness delay in seconds

# ---------------------------------------------------------------------------
# Asynchronous spinner ------------------------------------------------------
# ---------------------------------------------------------------------------
spinner_cycle = itertools.cycle("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")


def start_spinner(current_page_ref: List[int]) -> threading.Event:
    """Background thread that animates a spinner and current page number."""
    stop_event = threading.Event()

    def _spin() -> None:
        while not stop_event.is_set():
            frame = next(spinner_cycle)
            page_no = current_page_ref[0]
            sys.stdout.write(f"\r{frame}  Fetching page {page_no}   ")
            sys.stdout.flush()
            time.sleep(0.1)
        # clear line when done
        sys.stdout.write("\r" + " " * 40 + "\r")
        sys.stdout.flush()

    threading.Thread(target=_spin, daemon=True).start()
    return stop_event


# ---------------------------------------------------------------------------
# Scraper -------------------------------------------------------------------
# ---------------------------------------------------------------------------


def fetch_all_products(base: str) -> List[Dict[str, Any]]:
    """Iterate through a Shopify /products.json catalogue until empty page."""
    products: List[Dict[str, Any]] = []
    page_ref = [1]
    stop_spinner = start_spinner(page_ref)

    try:
        while True:
            try:
                resp = requests.get(
                    base, params={"limit": PAGE_LIMIT, "page": page_ref[0]}, timeout=15
                )
                resp.raise_for_status()
                chunk = resp.json().get("products", [])
            except requests.RequestException as err:
                stop_spinner.set()
                sys.stdout.write(f"\n❌  Error on page {page_ref[0]}: {err}\n")
                break

            if not chunk:
                break

            products.extend(chunk)
            page_ref[0] += 1
            time.sleep(SLEEP)
    finally:
        stop_spinner.set()

    sys.stdout.write(
        f"✅  Collected {len(products):,} products across {page_ref[0] - 1} pages.\n"
    )
    return products


# ---------------------------------------------------------------------------
# CLI -----------------------------------------------------------------------
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download cube listings from a chosen store (Shopify only)."
    )
    parser.add_argument(
        "store",
        choices=STORES.keys(),
        help="Short code of the cube store to scrape: "
        + ", ".join(
            f"{k} ({v.split('//')[1].split('/')[0]})" for k, v in STORES.items()
        ),
    )
    parser.add_argument(
        "--outfile",
        type=str,
        default=None,
        help="Output JSON file (defaults to <store>_products.json)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    base_url = STORES[args.store]
    out_file = args.outfile or f"{args.store}_products.json"

    all_products = fetch_all_products(base_url)
    pathlib.Path(out_file).write_text(json.dumps(all_products, indent=2))
    print(f"📄  Saved to {out_file}")
