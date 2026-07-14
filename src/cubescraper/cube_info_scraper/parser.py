import logging
from typing import Callable

from cubescraper.common.database_types import PublicCubeSurfaceFinishes
from cubescraper.common.exceptions import UnsupportedVendorError
from cubescraper.common.utils import get_hostname, get_parser
from cubescraper.cube_info_scraper.constants import (
    SURFACE_FINISH,
    WCA_LEGAL_CUBE_TYPES,
)
from cubescraper.cube_info_scraper.cube_info_types import (
    CubeInfoParserResult,
)
from cubescraper.cube_info_scraper.exceptions import (
    InvalidURLError,
    ParsingFailedError,
)
from cubescraper.cube_info_scraper.queries import get_enabled_vendors
from cubescraper.cube_info_scraper.parser_registry import PARSER_MAP

logger = logging.getLogger(__name__)


def detect_surface_finish(text: str) -> PublicCubeSurfaceFinishes | None:
    text = text.lower()
    for keyword, label in SURFACE_FINISH.items():
        if keyword in text:
            return label
    return None


def is_cube_wca_legal(cube_details: CubeInfoParserResult) -> bool | None:
    is_wca_legal = cube_details["wca_legal"] if "wca_legal" in cube_details else None

    if "type" in cube_details and cube_details["type"] in WCA_LEGAL_CUBE_TYPES:
        is_wca_legal = True

    if "smart" in cube_details and cube_details["smart"]:
        is_wca_legal = False

    return is_wca_legal


def resolve_parser(url: str) -> Callable[[str], CubeInfoParserResult | None]:
    hostname = (get_hostname(url) or "").lower()
    if not hostname:
        raise InvalidURLError(f"URL has no hostname: {url}")

    supported_vendors_hostnames = [
        vendor_hostname.lower()
        for url in get_enabled_vendors()
        if (vendor_hostname := get_hostname(url)) is not None
    ]

    if not any([hostname.endswith(supported_hostname) for supported_hostname in supported_vendors_hostnames]):
        raise UnsupportedVendorError(f"Vendor '{hostname}' is not supported.")

    return get_parser(hostname, PARSER_MAP)


def parse_cube_details(html: str, url: str) -> CubeInfoParserResult:
    parser = resolve_parser(url)

    logger.info("Started scraping cube info from HTML using %s", parser.__name__)
    cube_details = parser(html)
    logger.info("Finished scraping cube info from HTML file using %s", parser.__name__)
    if not cube_details:
        raise ParsingFailedError(f"Parser was unable to find cube details for: {url}")

    if "wca_legal" not in cube_details:
        wca_legal = is_cube_wca_legal(cube_details)
        if wca_legal is not None:
            cube_details["wca_legal"] = wca_legal

    return cube_details
