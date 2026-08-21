import logging
from typing import Callable, Optional

from bs4 import BeautifulSoup

from cubescraper.common.database_types import PublicCubeVendorLinksUpdate
from cubescraper.common.exceptions import UnsupportedVendorError
from cubescraper.common.utils import extract_number, get_hostname, get_parser
from cubescraper.price_tracker.parser_registry import PARSER_MAP
from cubescraper.price_tracker.price_types import ParseResult

logger = logging.getLogger(__name__)


def get_price_from_meta(soup: BeautifulSoup) -> float | None:
    price_meta_tag = soup.find("meta", property="product:price:amount") or soup.find(
        "meta", property="og:price:amount"
    )
    if price_meta_tag:
        raw = price_meta_tag.get("content")
        if isinstance(raw, str):
            return extract_number(raw)
        else:
            logger.warning("Couldn't extract price")
    else:
        logger.warning("Couldn't find price meta tag")


def get_currency_from_meta(soup: BeautifulSoup) -> str | None:
    meta_currency_tag = soup.find("meta", property="product:price:currency")
    if meta_currency_tag:
        meta_currency_content = meta_currency_tag.get("content")
        if isinstance(meta_currency_content, str):
            return meta_currency_content
        else:
            logger.warning("Couldn't extract currency")
    else:
        logger.warning("Couldn't find currency meta tag")


def resolve_vendor_parser(url: str) -> Optional[Callable[[str], ParseResult]]:
    host = (get_hostname(url) or "").lower()
    if not host:
        logger.warning("URL has no hostname: invalid URL given (%s)", url)
        return None

    try:
        return get_parser(host, PARSER_MAP)
    except UnsupportedVendorError as e:
        logger.warning(e)
    except Exception:
        logger.exception("An error occurred while retrieving parser for %s", host)

    return None


def parse_url(url: str, html: str) -> ParseResult:
    parser = resolve_vendor_parser(url)
    if not parser:
        raise UnsupportedVendorError("No parser for URL %s", url)

    logger.info("Parsing HTML content with %s", parser.__name__)
    try:
        return parser(html)
    except Exception:
        logger.exception(
            "An error occurred while parsing the HTML with %s",
            parser.__name__,
        )
        raise


def prepare_update_payload(
    id: int, price: float, availability: bool
) -> PublicCubeVendorLinksUpdate:
    return {
        "id": id,
        "available": availability,
        "price": price,
    }
