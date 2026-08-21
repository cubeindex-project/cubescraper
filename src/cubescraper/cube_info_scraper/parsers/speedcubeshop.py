import re
from urllib.parse import urljoin

from cubescraper.common.logging import logging, setup_logging
from cubescraper.common.utils import (
    clean_cube_type,
    extract_all_json_ld,
    extract_number,
    format_dimensions,
    fuzzy_pick,
    get_brand_from_json_ld,
    get_image_from_json_ld,
    get_name_from_json_ld,
    get_product_json_ld,
    soupify,
)
from cubescraper.cube_info_scraper.constants import (
    BALL_CORE,
    FUZZY_OVERRIDES,
    LIMITED,
    SMART,
)
from cubescraper.cube_info_scraper.cube_info_types import CubeInfoParserResult
from cubescraper.cube_info_scraper.parser import detect_surface_finish
from cubescraper.cube_info_scraper.queries import get_allowed_brands, get_allowed_types
from cubescraper.tools.test_parser import run_parser_test

logger = logging.getLogger(__name__)

SCS_TYPE_LABEL = ["type", "category"]


def parse_speedcubeshop(html: str) -> CubeInfoParserResult:
    soup = soupify(html)
    specs: CubeInfoParserResult = {}
    allowed_brands = get_allowed_brands()
    allowed_types = get_allowed_types()

    json_ld_tags = extract_all_json_ld(soup)
    product_json_ld = get_product_json_ld(json_ld_tags)
    if product_json_ld:
        name = get_name_from_json_ld(product_json_ld)
        if name:
            specs["name"] = name

        image = get_image_from_json_ld(product_json_ld)
        if image:
            specs["image_url"] = image

        brand = get_brand_from_json_ld(product_json_ld, allowed_brands)
        if brand:
            specs["brand"] = brand

    # Start scraping image URL
    if "image_url" not in specs:
        img = soup.find("img", class_="product-gallery__image")
        if img and img.get("src"):
            image_url = img["src"]
            if isinstance(image_url, str) and image_url.startswith("//"):
                specs["image_url"] = urljoin("https://speedcubeshop.com", image_url)
            elif isinstance(image_url, str):
                specs["image_url"] = image_url
        else:
            logger.warning("No image URL found in HTML")
    # End scraping image URL

    # Start scraping name
    if "name" not in specs:
        nameLbl = soup.find("h1", class_="product-meta__title heading h1")
        name = nameLbl.get_text(strip=True) if nameLbl else None
        if isinstance(name, str):
            specs["name"] = name
        else:
            logger.warning("No cube name found in HTML")
    # End scraping name

    # Start scraping features from name
    if "name" in specs:
        name_low = specs["name"].lower()

        if any(token in name_low for token in LIMITED):
            specs["version_type"] = "Limited"

        if "magnetic" in name_low:
            specs["magnetic"] = True

        if "maglev" in name_low:
            specs["maglev"] = True
            specs["magnetic"] = True

        if any(token in name_low for token in SMART):
            specs["smart"] = True

        if any(token in name_low for token in BALL_CORE):
            specs["ball_core"] = True

        detected_surface = detect_surface_finish(name_low)
        if detected_surface:
            specs["surface_finish"] = detected_surface
    else:
        logger.warning("Specs has no name: cannot scrap features from it.")
    # End scraping features from name

    description_block = soup.find(
        "div",
        class_="product-block-list__item product-block-list__item--description",
    )
    if description_block:
        landmark = description_block.find(
            string=re.compile(r"specs at a glance", re.IGNORECASE)
        )
        specs_list = landmark.find_next("ul") if landmark else None
        if specs_list:
            for spec in specs_list.find_all("li"):
                full_spec_text = spec.text
                spec_text_parts = full_spec_text.split(":", 1)
                if len(spec_text_parts) < 2:
                    logger.warning(
                        "Couldn't split label and value from full_spec_text: skipping."
                    )
                    continue
                spec_label = spec_text_parts[0].strip().lower()
                spec_text = spec_text_parts[1].strip().lower()
                if spec_label in SCS_TYPE_LABEL:
                    cleaned_type = clean_cube_type(spec_text)
                    type = fuzzy_pick(cleaned_type, allowed_types, FUZZY_OVERRIDES)
                    if type:
                        specs["type"] = type
                    else:
                        logger.warning("Cube type not found in description")
                elif spec_label == "size":
                    size = format_dimensions(spec_text)
                    if size:
                        specs["size"] = size
                    else:
                        logger.warning("Cube size not found in description")
                elif spec_label == "weight":
                    weight = extract_number(spec_text)
                    if weight:
                        specs["weight"] = weight
                    else:
                        logger.warning("Cube weight not found in description")
                elif spec_label == "finish":
                    if "surface_finish" not in specs:
                        detected_surface = detect_surface_finish(spec_text)
                        if detected_surface:
                            specs.setdefault("surface_finish", detected_surface)
                        else:
                            logger.warning(
                                "Cube's surface finish not found in description"
                            )
                else:
                    logger.info(
                        "Spec label (%s) doesn't match any known ones: skipping.",
                        spec_label,
                    )
                    continue
        else:
            logger.warning("Specs list not found")
    else:
        logger.warning("Description block not found")
    return specs


if __name__ == "__main__":
    setup_logging()

    run_parser_test(parse_speedcubeshop)
