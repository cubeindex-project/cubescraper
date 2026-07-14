import argparse
from importlib import import_module
import json
import re
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse
from uuid import UUID

from bs4 import BeautifulSoup
from rapidfuzz import fuzz, process

from cubescraper.common.logging import logging
from cubescraper.common.constants import NUMBER_REGEX
from cubescraper.common.exceptions import UnsupportedVendorError

logger = logging.getLogger(__name__)


def fuzzy_pick(
    value: str, allowed: list[str], overrides: dict[str, str] | None = None
) -> str | None:
    value = value.strip().lower()

    if not allowed:
        logger.warning("Allowed list is empty. Cannot fuzzy match.")
        return None

    if overrides and value in overrides:
        return overrides[value]

    result = process.extractOne(
        value,
        allowed,
        processor=lambda s: s.strip().lower(),
        scorer=fuzz.token_sort_ratio,
        score_cutoff=80,
    )

    if result is None:
        logger.warning("No fuzzy match found for '%s'. Allowed: %s", value, allowed)
        return None

    logger.debug(f"Fuzzy match results: {result}")

    match = result[0]

    return match


def get_short_uuid(uuid: UUID):
    return uuid.hex[:12]


def soupify(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def extract_all_json_ld(soup: BeautifulSoup):
    return soup.find_all("script", type="application/ld+json")


# TODO: make function handle json-ld's of type "@graph"
def get_product_json_ld(json_ld_tags) -> Optional[dict]:
    for json_ld_tag in json_ld_tags:
        json_ld = json.loads(json_ld_tag.text)
        if json_ld.get("@type") == "Product":
            logger.info("JSON-LD of type 'Product' found")
            logger.debug(
                "JSON-LD object of type Product: %s", json.dumps(json_ld, indent=4)
            )
            return json_ld


def get_name_from_json_ld(product_json_ld: dict) -> Optional[str]:
    name = product_json_ld.get("name")
    if name:
        return name
    else:
        logger.warning("No cube name found in JSON-LD")


def get_image_from_json_ld(product_json_ld: dict) -> Optional[str]:
    image = product_json_ld.get("image")
    if isinstance(image, list):
        return image[0]
    elif isinstance(image, str):
        return image
    else:
        logger.warning("No image URL found in JSON-LD")


def get_brand_from_json_ld(
    product_json_ld: dict, allowed_brands: List[str]
) -> Optional[str]:
    brand_data = product_json_ld.get("brand")
    if isinstance(brand_data, dict) and brand_data.get("@type") == "Brand":
        raw_brand = brand_data.get("name")
    elif isinstance(brand_data, str):
        raw_brand = brand_data
    else:
        logger.warning("No brand found in JSON-LD")
        raw_brand = None
    if raw_brand:
        normalized_brand = fuzzy_pick(raw_brand, allowed_brands)
        if normalized_brand:
            return normalized_brand
        else:
            logger.warning("Couldn't normalize brand from JSON-LD: %s", raw_brand)


def get_hostname(url: str) -> Optional[str]:
    parsed = urlparse(url)
    return parsed.hostname


def _normalize_number(raw: str) -> str:
    cleaned = raw.replace("\u00a0", "").replace(" ", "")
    separators = [i for i, char in enumerate(cleaned) if char in ",."]
    if not separators:
        return cleaned

    last_separator = separators[-1]
    decimals = len(cleaned) - last_separator - 1
    if decimals == 3 and len(separators) == 1:
        return cleaned.replace(cleaned[last_separator], "")

    integer_part = re.sub(r"[,.]", "", cleaned[:last_separator])
    decimal_part = cleaned[last_separator + 1 :]
    return f"{integer_part}.{decimal_part}"


def format_dimensions(text: str) -> str | None:
    if not text:
        logger.warning("No text provided")
        return None

    logger.debug("Raw input: %s", text)
    is_cm = "cm" in text.lower()
    text = re.sub(r"(?<=\d)\s*(mm|cm)\s*3\b", r"\1", text, flags=re.IGNORECASE)

    extracted_numbers = re.findall(NUMBER_REGEX, text)
    if not extracted_numbers:
        logger.warning("No numbers extracted")
        return None

    logger.debug("Extracted numbers: %s", extracted_numbers)

    processed_parts = []
    for num in extracted_numbers:
        value = float(_normalize_number(num))
        if is_cm:
            value = convert_cm_to_mm(value)

        if value.is_integer():
            processed_parts.append(str(int(value)))
        else:
            processed_parts.append(str(value))

    if not processed_parts:
        return None

    if len(processed_parts) == 1:
        processed_parts = [processed_parts[0]] * 3
    elif len(processed_parts) == 2:
        processed_parts.append(processed_parts[-1])
    else:
        processed_parts = processed_parts[:3]

    logger.debug("Final processed parts: %s", processed_parts)
    return " x ".join(processed_parts)


def extract_number(value: str) -> float | None:
    match = re.search(NUMBER_REGEX, value)
    if not match:
        return None

    raw = match.group(1)
    logger.debug("Matched raw number: %s", raw)

    cleaned = _normalize_number(raw)
    logger.debug("Cleaned number: %s", cleaned)

    return float(cleaned)


def clean_cube_type(text: str) -> str:
    text = text.lower().strip()

    noise_pattern = r"\b(cubes|cube|speed|magnetic|stickerless|pro)\b"
    text = re.sub(noise_pattern, "", text)

    return text


def get_parser(hostname: str, PARSER_MAP: Dict[str, str]) -> Callable[[str], Any]:
    for domain_suffix, dotted in PARSER_MAP.items():
        if hostname.endswith(domain_suffix):
            module_name, func_name = dotted.split(":", 1)
            try:
                module = import_module(module_name)
            except ImportError as e:
                raise Exception(
                    f"Failed to import parser module for {domain_suffix}"
                ) from e

            try:
                parser_func = getattr(module, func_name)
            except AttributeError as e:
                raise Exception(
                    f"Parser function {func_name} not found in {module_name}"
                ) from e

            return parser_func

    raise UnsupportedVendorError("No parser registered for hostname (%s)", hostname)


def convert_cm_to_mm(cm_value: float):
    return cm_value * 10


def non_negative_int(value):
    ivalue = int(value)
    if ivalue < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return ivalue


def non_negative_float(value):
    ivalue = float(value)
    if ivalue < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return ivalue
