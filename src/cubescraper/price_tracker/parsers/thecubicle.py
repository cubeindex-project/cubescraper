import re

from cubescraper.common.parser import soupify
from cubescraper.price_tracker.price_types import ParseResult
from cubescraper.tools.test_parser import run_parser_test

available_keyword = [
    "http://schema.org/InStock",
    "http://schema.org/MadeToOrder",
    "http://schema.org/OnlineOnly",
    "http://schema.org/PreOrder",
    "http://schema.org/PreSale",
]

unavailable_keyword = [
    "http://schema.org/SoldOut",
    "http://schema.org/OutOfStock",
    "http://schema.org/Discontinued",
    "http://schema.org/Reserved",
    "http://schema.org/LimitedAvailability",
    "http://schema.org/InStoreOnly",
    "http://schema.org/BackOrder",
]


def parse_thecubicle(
    html: str,
) -> ParseResult:
    soup = soupify(html)

    price_tag = soup.find("meta", attrs={"itemprop": "price"})
    availability_tag = soup.find("link", attrs={"itemprop": "availability"})

    price, availability, availability_url = None, None, None

    if availability_tag:
        availability_url = availability_tag.get("href")

    if availability_url in available_keyword:
        availability = True
    elif availability_url in unavailable_keyword:
        availability = False
    else:
        availability = None

    if price_tag:
        raw = price_tag.get("content")
        if raw:
            raw = re.sub(r"[^\d.,]", "", str(raw)).replace(",", ".")
            try:
                price = float(raw)
            except Exception:
                price = None

    return ParseResult(price, availability)


if __name__ == "__main__":
    run_parser_test(parse_thecubicle)
