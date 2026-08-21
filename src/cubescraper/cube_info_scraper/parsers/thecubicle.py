from urllib.parse import urljoin

from cubescraper.common.logging import logging, setup_logging
from cubescraper.common.utils import (
    extract_number,
    format_dimensions,
    fuzzy_pick,
    soupify,
)
from cubescraper.cube_info_scraper.constants import (
    BALL_CORE,
    FUZZY_OVERRIDES,
    LIMITED,
    SMART,
    TRANSPARENT,
)
from cubescraper.cube_info_scraper.cube_info_types import CubeInfoParserResult
from cubescraper.cube_info_scraper.parser import detect_surface_finish
from cubescraper.cube_info_scraper.queries import get_allowed_brands, get_allowed_types
from cubescraper.tools.test_parser import run_parser_test

logger = logging.getLogger(__name__)


def parse_thecubicle(html: str) -> CubeInfoParserResult:
    soup = soupify(html)
    specs: CubeInfoParserResult = {}
    allowed_brands = get_allowed_brands()
    allowed_types = get_allowed_types()

    # TheCubicle doesn't provide a JSON-LD object from which we can scrape from.

    name_label = soup.find("h1", {"itemprop": "name"})
    name = name_label.get_text(strip=True) if name_label else None

    if name:
        specs["name"] = name

        name_low = name.lower()

        if "maglev" in name_low:
            specs["maglev"] = True
            specs["magnetic"] = True

        if "magnetic" in name_low:
            specs["magnetic"] = True

        if any(token in name_low for token in SMART):
            specs["smart"] = True
            specs["wca_legal"] = False

        if any(token in name_low for token in TRANSPARENT):
            specs["wca_legal"] = False

        if any(token in name_low for token in BALL_CORE):
            specs["ball_core"] = True

        if any(token in name_low for token in LIMITED):
            specs["version_type"] = "Limited"

        detected_surface_finish = detect_surface_finish(name)
        if detected_surface_finish:
            specs["surface_finish"] = detected_surface_finish
    else:
        logger.warning("No cube name found in HTML")

    description_div = soup.find("div", id="description-tab")
    if description_div:
        description = description_div.get_text(" ", strip=True)

        if description:
            detected_surface_finish = detect_surface_finish(description)
            if detected_surface_finish:
                specs.setdefault("surface_finish", detected_surface_finish)

    meta = soup.find("meta", {"itemprop": "image"})
    if meta:
        image_url = meta.get("content", None)
        if isinstance(image_url, str):
            specs["image_url"] = urljoin("https://www.thecubicle.com", image_url)

    table = soup.select_one("table.w-full.border-collapse.border.border-gray-200")

    for tr in table.select("tr") if table else []:
        th = tr.find("th")
        td = tr.find("td")
        if not th or not td:
            continue

        # Decompose superscript and subscript tags to prevent text like
        # "56.0mm³" from turning into "56.0mm 3" when extracting text.
        for sup in td.find_all("sup"):
            sup.decompose()
        for sub in td.find_all("sub"):
            sub.decompose()

        label = th.get_text(strip=True)
        value = td.get_text(separator=" ", strip=True)
        key = label.lower()

        if key in {"manufacturer", "brand"}:
            brand = fuzzy_pick(value, allowed_brands)
            if brand is None:
                continue
            specs["brand"] = brand

        elif key in {"type"}:
            type = fuzzy_pick(value, allowed_types, FUZZY_OVERRIDES)
            if type is None:
                continue
            specs["type"] = type

        elif key in {"added"}:
            specs["release_date"] = value

        elif key in {"magnets"}:
            specs["magnetic"] = "magnetic" in value.lower() or value.lower() == "yes"

        elif key in {"dimensions"}:
            normalized_dimensions = format_dimensions(value)
            if normalized_dimensions:
                specs["size"] = normalized_dimensions
            else:
                logger.warning("Couldn't normalize dimension: (%s)", value)

        elif key in {"item weight"}:
            numeric_value = extract_number(value)
            if numeric_value:
                specs["weight"] = numeric_value
            else:
                logger.warning("Couldn't extract weight from value: (%s)", value)

        else:
            logger.info("Table key (%s) doesn't match any known one: skipping.", key)
            continue

    return specs


if __name__ == "__main__":
    setup_logging()

    run_parser_test(
        parse_thecubicle,
        "https://www.thecubicle.com/en-global/products/yj-yuhu-megaminx-v3-magnetic",
    )
