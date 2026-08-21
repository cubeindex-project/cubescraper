from __future__ import annotations

from cubescraper.common.logging import logging, setup_logging
from cubescraper.common.utils import (
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
from cubescraper.cube_info_scraper.cube_info_types import CubeInfoParserResult
from cubescraper.cube_info_scraper.queries import (
    get_allowed_brands,
)
from cubescraper.tools.test_parser import run_parser_test

logger = logging.getLogger(__name__)


def parse_kewbz(html: str) -> CubeInfoParserResult:
    soup = soupify(html)

    allowed_brands = get_allowed_brands()

    specs: CubeInfoParserResult = {}

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

    specs_accordion_panel = soup.select_one('div[id^="ProductAccordion-table_"]')
    if specs_accordion_panel:
        specs_table = specs_accordion_panel.find("tbody")
        table_rows = specs_table.find_all("tr") if specs_table else None
        if table_rows:
            for row in table_rows:
                key_tag = row.find("th")
                value_tag = row.find("td")
                if not key_tag or not value_tag:
                    logger.warning("Missing key or value in table row: %s", row)
                    continue

                key = key_tag.get_text(strip=True).lower()
                value = value_tag.get_text(strip=True)

                if key == "size":
                    normalized_dimensions = format_dimensions(value)
                    if normalized_dimensions:
                        specs["size"] = normalized_dimensions
                    else:
                        logger.warning("Couldn't normalize dimension: (%s)", value)
                elif key == "weight":
                    numeric_value = extract_number(value)
                    if numeric_value:
                        specs["weight"] = numeric_value
                    else:
                        logger.warning(
                            "Couldn't extract weight from value: (%s)", value
                        )
                elif key == "magnetic":
                    specs["magnetic"] = value.lower() == "magnetic"
                elif "brand" not in specs and key == "vendor":
                    brand = fuzzy_pick(value, allowed_brands)
                    if brand:
                        specs.setdefault("brand", brand)
                    else:
                        logger.warning("Couldn't normalize brand: (%s)", value)
                else:
                    logger.info(
                        "Table key (%s) doesn't match any known one: skipping.", key
                    )
                    continue
        else:
            logger.warning("No table rows found in the specs table")
    else:
        logger.warning("No specs accordion panel found in the HTML")

    return specs


if __name__ == "__main__":
    setup_logging()

    run_parser_test(
        parse_kewbz, "https://kewbz.co.uk/collections/nxn-events/products/yj-mgc-4x4-m"
    )
