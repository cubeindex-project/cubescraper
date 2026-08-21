from cubescraper.common.logging import logging, setup_logging
from cubescraper.common.utils import soupify
from cubescraper.price_tracker.constants import (
    JSON_LD_AVAILABLE_KEYWORDS,
)
from cubescraper.price_tracker.parser import get_price_from_meta
from cubescraper.price_tracker.price_types import ParseResult
from cubescraper.tools.test_parser import run_parser_test

logger = logging.getLogger(__name__)


def parse_thecubicle(
    html: str,
) -> ParseResult:
    soup = soupify(html)

    price, availability = None, None

    availability_tag = soup.find("link", attrs={"itemprop": "availability"})
    if availability_tag:
        availability_url = availability_tag.get("href")

        if isinstance(availability_url, str):
            availability = any(
                availability_url.endswith(keyword)
                for keyword in JSON_LD_AVAILABLE_KEYWORDS
            )
        else:
            logger.warning("Couldn't extract availability")

    price = get_price_from_meta(soup)

    return ParseResult(price, availability)


if __name__ == "__main__":
    setup_logging()

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("supabase").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    run_parser_test(parse_thecubicle)
