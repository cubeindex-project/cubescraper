from cubescraper.common.parser import extract_number, format_dimensions, soupify
from cubescraper.cube_info_scraper.constants import (
    BALL_CORE,
    LIMITED,
    SMART,
    TRANSPARENT,
)
from cubescraper.cube_info_scraper.cube_info_types import ParserResult
from cubescraper.cube_info_scraper.parser import detect_surface_finish, fuzzy_pick
from cubescraper.cube_info_scraper.queries import get_allowed_brands, get_allowed_types
from cubescraper.tools.test_parser import run_parser_test


def parse_thecubicle(html: str) -> ParserResult:
    soup = soupify(html)
    specs: ParserResult = {}
    allowed_brands = get_allowed_brands()
    allowed_types = get_allowed_types()

    nameLbl = soup.find("h1", {"itemprop": "name"})
    name = nameLbl.get_text(strip=True) if nameLbl else None

    if name is not None:
        nameLow = name.lower()

        if "maglev" in nameLow:
            specs["maglev"] = True

        if any(k in nameLow for k in SMART):
            specs["smart"] = True
            specs["wca_legal"] = False

        if any(k in nameLow for k in TRANSPARENT):
            specs["wca_legal"] = False

        if any(k in nameLow for k in BALL_CORE):
            specs["ball_core"] = True

        if any(k in nameLow for k in LIMITED):
            specs["version_type"] = "Limited"

        detected_surface_finish = detect_surface_finish(name)
        if detected_surface_finish:
            specs["surface_finish"] = detected_surface_finish

    description_div = soup.find("div", id="description-tab")
    if description_div:
        h3 = description_div.find("h3", string="Product Description")  # type: ignore
        if h3:
            h3.parent.decompose()

        description = description_div.get_text(" ", strip=True)
    else:
        description = None

    if description:
        detected_surface_finish = detect_surface_finish(description)
        if detected_surface_finish:
            specs.setdefault("surface_finish", detected_surface_finish)

    meta = soup.find("meta", {"itemprop": "image"})
    if meta:
        content = meta.get("content", None)
        if content:
            specs["image_url"] = "https:" + str(content)

    table = soup.select_one("table.w-full.border-collapse.border.border-gray-200")

    for tr in table.select("tr") if table else []:
        th = tr.find("th")
        td = tr.find("td")
        if not th or not td:
            continue

        label = th.get_text(strip=True)
        value = td.get_text(separator=" ", strip=True)
        key = label.lower()

        if key in {"manufacturer", "brand"}:
            brand = fuzzy_pick(value, allowed_brands)
            if brand is None:
                continue
            specs["brand"] = brand

        elif key in {"type"}:
            type = fuzzy_pick(value, allowed_types)
            if type is None:
                continue
            specs["type"] = type

        elif key in {"added"}:
            specs["release_date"] = value

        elif key in {"magnets"}:
            specs["magnetic"] = value.lower() == "magnetic"

        elif key in {"dimensions"}:
            specs["size"] = format_dimensions(value)

        elif key in {"item weight"}:
            numeric_value = extract_number(value)
            if numeric_value is not None:
                specs["weight"] = numeric_value

        else:
            continue

    return specs


if __name__ == "__main__":
    run_parser_test(parse_thecubicle)
