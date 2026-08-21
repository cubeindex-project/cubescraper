from __future__ import annotations

from cubescraper.common.logging import logging, setup_logging
from cubescraper.common.utils import soupify
from cubescraper.price_tracker.constants import ATOUTCUBES_DEFAULT_CURRENCY
from cubescraper.price_tracker.parser import (
    get_currency_from_meta,
    get_price_from_meta,
)
from cubescraper.price_tracker.price_types import ParseResult
from cubescraper.tools.test_parser import run_parser_test

logger = logging.getLogger(__name__)


def parse_atoutcubes(html: str) -> ParseResult:
    soup = soupify(html)

    price: float | None = None
    availability: bool | None = None

    price = get_price_from_meta(soup)

    availability_badge = soup.find("span", id="product-availability")
    if availability_badge:
        availability_badge_text = availability_badge.text
        if isinstance(availability_badge_text, str):
            availability = availability_badge_text.strip().lower() != "out-of-stock"
        else:
            logger.warning("Couldn't extract availability")

    currency = get_currency_from_meta(soup)
    if currency and currency != ATOUTCUBES_DEFAULT_CURRENCY:
        logger.warning(
            "Unexpected currency: expected=%s actual=%s",
            ATOUTCUBES_DEFAULT_CURRENCY,
            currency,
        )
        return ParseResult(None, availability)

    return ParseResult(price=price, availability=availability)


if __name__ == "__main__":
    setup_logging()

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("supabase").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    run_parser_test(parse_atoutcubes)
