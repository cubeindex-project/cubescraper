import logging
from importlib import import_module
from typing import Callable, Optional

from rapidfuzz import fuzz, process

from cubescraper.common.parser import get_hostname
from cubescraper.cube_info_scraper.constants import (
    FUZZY_OVERRIDES,
    SUPPORTED_VENDORS,
    SURFACE_FINISH,
)
from cubescraper.cube_info_scraper.cube_info_types import (
    CubeSurfaceFinish,
    ParserResult,
)

logger = logging.getLogger(__name__)


def resolve_parser(url: str) -> Optional[Callable[[str], ParserResult | None]]:
    hostname = (get_hostname(url) or "").lower()
    if not hostname:
        logger.warning("URL has no hostname — invalid URL given: %r", url)
        return

    for domain_suffix, dotted in SUPPORTED_VENDORS.items():
        if hostname.endswith(domain_suffix):
            module_name, func_name = dotted.split(":", 1)
            try:
                module = import_module(module_name)
            except ImportError as e:
                logger.exception(
                    "Failed to import parser module for domain %s: %s", domain_suffix, e
                )
                return

            try:
                parser_func = getattr(module, func_name)
            except AttributeError:
                logger.error(
                    "Parser function %r not found in module %r for domain %s",
                    func_name,
                    module_name,
                    domain_suffix,
                )
                return

            return parser_func

    logger.info("No parser registered for hostname %r (%s)", hostname, url)
    return


def parse_cube_details(html: str, url: str) -> ParserResult | None:
    cube_details: ParserResult | None = None

    parser = resolve_parser(url)
    if parser is None:
        logger.warning("No parser implemented for %s", url)
        return None

    cube_details = parser(html)
    if cube_details is None:
        logger.warning("No cube details found for %s", url)
        return None

    logger.debug("Link processed (%s).", url)

    return cube_details


def fuzzy_pick(value: str, allowed: list[str]) -> str | None:
    value = value.strip()

    if not allowed:
        logger.warning("Allowed list is empty. Cannot fuzzy match.")
        return None

    if value in FUZZY_OVERRIDES:
        return FUZZY_OVERRIDES[value]

    result = process.extractOne(value, allowed, scorer=fuzz.token_sort_ratio)

    if result is None:
        logger.warning("No fuzzy match found for '%s'. Allowed: %s", value, allowed)
        return None

    match = result[0]

    return match


def detect_surface_finish(text: str) -> CubeSurfaceFinish | None:
    text = text.lower()
    for keyword, label in SURFACE_FINISH.items():
        if keyword in text:
            return label
    return None
