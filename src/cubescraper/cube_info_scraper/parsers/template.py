from __future__ import annotations

from cubescraper.common.logging import logging, setup_logging
from cubescraper.common.utils import soupify
from cubescraper.cube_info_scraper.cube_info_types import CubeInfoParserResult
from cubescraper.cube_info_scraper.queries import (
    get_allowed_brands,
    get_allowed_types,
)
from cubescraper.tools.test_parser import run_parser_test

# Initialize a logger specific to this module's name for tracking execution flow
logger = logging.getLogger(__name__)


def parser(html: str) -> CubeInfoParserResult:
    """
    Parse a cube store product page and extract its price + availability.
    """
    # Convert the raw HTML string into a navigable BeautifulSoup object
    soup = soupify(html)  # noqa: F841 <- Please remove this comment

    # Retrieve lists of valid brands and cube types to validate parsed data against
    allowed_brands = get_allowed_brands()  # noqa: F841 <- Please remove this comment
    allowed_types = get_allowed_types()  # noqa: F841 <- Please remove this comment

    # Initialize the return variable with an empty dictionary conforming to CubeInfoParserResult
    specs: CubeInfoParserResult = {}

    # ---------------------------------------------------------
    #  INSERT YOUR PARSING LOGIC HERE
    # ---------------------------------------------------------

    return specs


if __name__ == "__main__":
    # Configure the global logging settings (format, levels, handlers)
    setup_logging()

    # Runs validation, prints sample output, ensures parser works correctly.
    run_parser_test(parser)
