from __future__ import annotations

from cubescraper.common.utils import soupify
from cubescraper.price_tracker.price_types import ParseResult
from cubescraper.tools.test_parser import run_parser_test
from src.cubescraper.common.logging import logging, setup_logging

logger = logging.getLogger(__name__)


def parser(html: str) -> ParseResult:
    """
    Parse a cube store product page and extract its price + availability.
    """
    soup = soupify(html)  # noqa: F841 <- Please remove this comment

    # Default values (None = "parser did not find anything")
    price: float | None = None
    availability: bool | None = None

    # ---------------------------------------------------------
    #  INSERT YOUR PARSING LOGIC HERE
    #
    #  Example:
    #  price_el = soup.select_one(".product-price")
    #  if price_el:
    #      price = float(price_el.text.strip().replace("$", ""))
    #
    #  availability_el = soup.select_one(".availability")
    #  if availability_el:
    #      availability = "in stock" in availability_el.text.lower()
    #
    # ---------------------------------------------------------

    return ParseResult(price=price, availability=availability)


if __name__ == "__main__":
    # Configure the global logging settings (format, levels, handlers)
    setup_logging()

    # Suppress verbose debug logs from third-party libraries by setting them to WARNING
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("supabase").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    # Runs validation, prints sample output, ensures parser works correctly.
    run_parser_test(parser)
