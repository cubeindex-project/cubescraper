from __future__ import annotations

from cubescraper.common.logging import logging, setup_logging
from cubescraper.common.utils import soupify
from cubescraper.price_tracker.parser import get_price_from_meta
from cubescraper.price_tracker.price_types import ParseResult
from cubescraper.tools.test_parser import run_parser_test

logger = logging.getLogger(__name__)


def parse_kewbz(html: str) -> ParseResult:
    soup = soupify(html)

    price: float | None = None
    availability: bool | None = None

    price = get_price_from_meta(soup)

    availability_pill = soup.find("div", class_="product__inventory")
    if availability_pill:
        availability_pill_text = availability_pill.text
        if isinstance(availability_pill_text, str):
            availability = availability_pill_text.strip().lower() != "out of stock"

    return ParseResult(price=price, availability=availability)


if __name__ == "__main__":
    setup_logging()

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("supabase").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    run_parser_test(parse_kewbz)
