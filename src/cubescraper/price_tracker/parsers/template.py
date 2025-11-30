from __future__ import annotations

from cubescraper.price_tracker.parser import soupify
from cubescraper.price_tracker.price_types import ParseResult
from cubescraper.tools.test_parser import run_parser_test


def parser(html: str) -> ParseResult:
    """
    Parse a cube store product page and extract its price + availability.
    """
    soup = soupify(html)  # noqa: F841 <- Please remove this line

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
    # Runs validation, prints sample output, ensures parser works correctly.
    run_parser_test(parser)
