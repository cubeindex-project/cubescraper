import re

from cubescraper.common.parser import soupify
from cubescraper.price_tracker.price_types import ParseResult
from cubescraper.tools.test_parser import run_parser_test


def parse_scs(
    html: str,
) -> ParseResult:
    soup = soupify(html)

    price_tag = (
        soup.find("meta", {"itemprop": "price"})  # meta content
        or soup.find("span", {"itemprop": "price"})
        or soup.find("span", class_="money")
    )
    availability_tag = soup.find("input", {"id": "product-add-to-cart"})

    price, availability = None, None

    if availability_tag:
        val = availability_tag.get("value", "") or ""
        availability = str(val).strip().lower() == "add to cart"

    if price_tag:
        raw = (
            price_tag.get("content")
            if price_tag.name == "meta"
            else price_tag.get_text()
        )
        if raw:
            raw = re.sub(r"[^\d.,]", "", str(raw)).replace(",", ".")
            try:
                price = float(raw)
            except Exception:
                price = None

    return ParseResult(price, availability)


if __name__ == "__main__":
    run_parser_test(parse_scs)
