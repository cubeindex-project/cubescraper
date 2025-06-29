import sys
import time
import itertools
import json
import pathlib
import threading
from typing import List, Dict, Any

import requests

# ---------------------------------------------------------------------------
# Config --------------------------------------------------------------------
# ---------------------------------------------------------------------------
BASE = "https://speedcubeshop.com/products.json"
PAGE_LIMIT = 250
SLEEP = 0.7  # seconds between requests (soft‑throttle)

# ---------------------------------------------------------------------------
# Asynchronous spinner ------------------------------------------------------
# ---------------------------------------------------------------------------

spinner_cycle = itertools.cycle("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")  # braille frames


def start_spinner(current_page_ref: List[int]) -> threading.Event:
    """Launch a background thread that animates a spinner.

    Args:
        current_page_ref: a single‑element list whose 0‑index holds the current
            page number. Using a mutable list sidesteps global variables while
            letting the main thread update the number the spinner displays.
    Returns:
        A threading.Event that the caller must .set() to stop the spinner.
    """
    stop_event = threading.Event()

    def _spin() -> None:
        while not stop_event.is_set():
            frame = next(spinner_cycle)
            page_no = current_page_ref[0]
            sys.stdout.write(f"\r{frame}  Fetching page {page_no}   ")
            sys.stdout.flush()
            time.sleep(0.1)  # frame rate ~10 fps
        # clear line when done
        sys.stdout.write("\r" + " " * 40 + "\r")
        sys.stdout.flush()

    threading.Thread(target=_spin, daemon=True).start()
    return stop_event


# ---------------------------------------------------------------------------
# Scraper -------------------------------------------------------------------
# ---------------------------------------------------------------------------


def fetch_all_products(base: str = BASE) -> List[Dict[str, Any]]:
    products: List[Dict[str, Any]] = []
    page_ref = [1]  # mutable reference for spinner thread
    stop_spinner = start_spinner(page_ref)

    try:
        while True:
            try:
                resp = requests.get(
                    base,
                    params={"limit": PAGE_LIMIT, "page": page_ref[0]},
                    timeout=15,
                )
                resp.raise_for_status()
                chunk = resp.json().get("products", [])
            except requests.RequestException as err:
                stop_spinner.set()
                sys.stdout.flush()
                sys.stdout.write(f"\n❌  Error on page {page_ref[0]}: {err}\n")
                break

            if not chunk:
                break

            products.extend(chunk)
            page_ref[0] += 1
            time.sleep(SLEEP)
    finally:
        stop_spinner.set()

    sys.stdout.flush()
    sys.stdout.write(
        f"✅  Collected {len(products):,} products across {page_ref[0] - 1} pages.\n"
    )
    return products


# ---------------------------------------------------------------------------
# Main ----------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    all_products = fetch_all_products()
    pathlib.Path("scs_products.json").write_text(json.dumps(all_products, indent=2))

# spec = (
#     "title",
#     "handle",
#     "vendor",
#     "published_at",
#     "product_type",
#     "tags",
#     "variants",
#     "images",
#     "options",
# )
# clean = glom(products, spec)
# out.extend(clean)
