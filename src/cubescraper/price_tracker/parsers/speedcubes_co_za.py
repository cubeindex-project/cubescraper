from cubescraper.common.logging import logging, setup_logging
from cubescraper.common.utils import soupify
from cubescraper.price_tracker.parser import get_price_from_meta
from cubescraper.price_tracker.price_types import ParseResult
from cubescraper.tools.test_parser import run_parser_test

logger = logging.getLogger(__name__)


def parse_speedcubes_co_za(
    html: str,
) -> ParseResult:
    soup = soupify(html)

    price, availability = None, None

    price = get_price_from_meta(soup)

    availability_tag = soup.find(
        "button",
        class_="add-to-cart",
    )
    if availability_tag:
        availability_span = availability_tag.find("span", class_="button__text")
        if availability_span:
            availability_string = availability_span.text.strip().lower()
            availability = availability_string == "add to cart"
        else:
            logger.warning("Couldn't find availability")
    else:
        logger.warning("Couldn't find add to cart button")

    return ParseResult(price, availability)


if __name__ == "__main__":
    setup_logging()

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("supabase").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    run_parser_test(parse_speedcubes_co_za)
