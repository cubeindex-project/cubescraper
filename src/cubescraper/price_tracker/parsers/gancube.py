import re

from cubescraper.common.parser import soupify
from cubescraper.price_tracker.price_types import ParseResult
from cubescraper.tools.test_parser import run_parser_test


def parse_gancube(
    html: str,
) -> ParseResult:
    soup = soupify(html)

    price_tag = (
        soup.find("span", class_="price-item--sale")
        or soup.find("span", class_="price-item--regular")
        or soup.find("meta", attrs={"itemprop": "price"})
    )
    availability_tag = soup.find("button", class_="product-form__submit")

    price, availability = None, None

    if availability_tag:
        availability = not availability_tag.has_attr("disabled")

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
    run_parser_test(parse_gancube)
