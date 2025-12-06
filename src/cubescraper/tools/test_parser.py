from typing import Callable, Optional

from cubescraper.common.http import fetch_web_page


def run_parser_test(parser: Callable[[str], Optional[object]]) -> Optional[object]:
    """
    Simple CLI helper to test a parser against a single product page URL.
    - Asks for a URL
    - Fetches the HTML
    - Runs the parser
    - Prints and returns the result
    """
    print("=== Parser tester ===")
    print("Paste a product page URL to test your parser.")
    print("Press Enter on an empty line to cancel.\n")

    link = input("Product page URL: ").strip()
    if not link:
        print("No URL entered. Aborting.")
        return None

    print("\n[1/3] Fetching page...")
    html = fetch_web_page(link)
    if not html:
        print("[ERROR] Failed to fetch the page (empty or None response).")
        return None

    print("[2/3] Running parser...")
    try:
        result = parser(html)
    except Exception as e:
        print(f"[ERROR] Exception while parsing page: {e}")
        return None

    print("[3/3] Parser result:\n")
    print(result)
    print("\n=== Done ===")

    # Also return the result so you can inspect it in a REPL or tests
    return result
