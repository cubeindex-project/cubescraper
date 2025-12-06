import re

from cubescraper.common.parser import soupify
from cubescraper.price_tracker.price_types import ParseResult
from cubescraper.tools.test_parser import run_parser_test


def parse_speedcubes_co_za(
    html: str,
) -> ParseResult:
    soup = soupify(html)

    price_tag = soup.find("span", class_="product-price--original")
    availability_tag = soup.find("button", class_="add-to-cart")

    price, availability = None, None

    if availability_tag:
        availability = not availability_tag.has_attr("disabled")

    if price_tag:
        raw = price_tag.get_text()
        if raw:
            raw = re.sub(r"[^\d.,]", "", raw).replace(",", ".")
            try:
                price = float(raw)
            except Exception:
                price = None

    return ParseResult(price, availability)


if __name__ == "__main__":
    run_parser_test(parse_speedcubes_co_za)
