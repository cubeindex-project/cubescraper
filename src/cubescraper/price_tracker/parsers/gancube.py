from cubescraper.common.logging import logging, setup_logging
from cubescraper.common.utils import extract_number, soupify
from cubescraper.price_tracker.price_types import ParseResult
from cubescraper.tools.test_parser import run_parser_test

logger = logging.getLogger(__name__)


def parse_gancube(
    html: str,
) -> ParseResult:
    soup = soupify(html)

    price, availability = None, None

    price_container = soup.find("div", class_="price__regular")
    if price_container:
        raw_price_value = price_container.find("span", class_="price-item")

        if raw_price_value:
            price = extract_number(raw_price_value.text)
        else:
            logger.warning("Couldn't find price value span inside price container")
    else:
        logger.warning("Couldn't find price container")

    add_to_cart_button = soup.find("button", class_="product-form__submit")
    if add_to_cart_button:
        availability = not add_to_cart_button.has_attr("disabled")
    else:
        logger.warning("Couldn't find add to cart button to determine availability")

    return ParseResult(price, availability)


if __name__ == "__main__":
    setup_logging()

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("supabase").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    run_parser_test(parse_gancube)
