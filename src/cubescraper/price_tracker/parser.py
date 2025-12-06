import logging
from importlib import import_module
from typing import Callable, Optional

from cubescraper.common.parser import get_hostname
from cubescraper.price_tracker.constants import SUPPORTED_VENDORS
from cubescraper.price_tracker.price_types import CubeVendorLinkPayload, ParseResult

logger = logging.getLogger(__name__)


def resolve_vendor_parser(url: str) -> Optional[Callable[[str], ParseResult]]:
    host = (get_hostname(url) or "").lower()
    if not host:
        logger.warning(
            "resolve_vendor_parser: URL has no hostname — invalid URL given: %r", url
        )
        return None

    for domain_suffix, dotted in SUPPORTED_VENDORS.items():
        if host.endswith(domain_suffix):
            module_name, func_name = dotted.split(":", 1)
            try:
                module = import_module(module_name)
            except ImportError as e:
                logger.exception(
                    "Failed to import parser module for domain %s: %s",
                    domain_suffix,
                    e,
                )
                return None

            try:
                parser_func = getattr(module, func_name)
            except AttributeError:
                logger.error(
                    "Parser function %r not found in module %r for domain %s",
                    func_name,
                    module_name,
                    domain_suffix,
                )
                return None

            return parser_func

    logger.info("No parser registered for hostname %r (%s)", host, url)
    return None


def parse_url(url: str, html: str, debug: bool = False) -> ParseResult:
    parser = resolve_vendor_parser(url)
    if not parser:
        logger.debug("No parser for URL %s — skipping", url)
        return ParseResult(None, None)

    result = ParseResult(None, None)

    if parser:
        try:
            result = parser(html)
        except Exception:
            if debug:
                logger.debug("%s tried to parse %s", parser.__name__, url)
                logger.exception("Parse error")
            else:
                logger.warning(
                    "An error occurred while parsing the HTML for %s — skipping (use --debug for details)",
                    url,
                )
            return ParseResult(None, None)

    return ParseResult(price=result.price, availability=result.availability)


def prepare_update_payload(
    id: int, price: float, availability: bool
) -> CubeVendorLinkPayload:
    return {
        "id": id,
        "available": availability,
        "price": price,
    }
