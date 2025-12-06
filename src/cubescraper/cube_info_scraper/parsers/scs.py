from cubescraper.common.parser import extract_number, format_dimensions, soupify
from cubescraper.cube_info_scraper.constants import BALL_CORE, LIMITED, SMART
from cubescraper.cube_info_scraper.cube_info_types import ParserResult
from cubescraper.cube_info_scraper.parser import fuzzy_pick
from cubescraper.cube_info_scraper.queries import get_allowed_brands, get_allowed_types
from cubescraper.tools.test_parser import run_parser_test


def parse_scs(html: str) -> ParserResult:
    soup = soupify(html)
    specs: ParserResult = {}
    allowed_brands = get_allowed_brands()
    allowed_types = get_allowed_types()

    img = soup.select_one("img[id^='product-featured-image']")

    if img and img.get("src"):
        image_url = img["src"]
        if isinstance(image_url, str) and image_url.startswith("//"):
            specs["image_url"] = "https:" + image_url
        elif isinstance(image_url, str):
            specs["image_url"] = image_url

    nameLbl = soup.select_one("h1.product-title")
    name = nameLbl.get_text(strip=True) if nameLbl else None

    if name is not None:
        nameLow = name.lower()

        if "uv coated" in nameLow:
            specs["surface_finish"] = "UV Coated"
        if any(token in nameLow for token in LIMITED):
            specs["version_type"] = "Limited"
        if "magnetic" in nameLow:
            specs["magnetic"] = True
        if "maglev" in nameLow:
            specs["maglev"] = True
        if any(token in nameLow for token in SMART):
            specs["smart"] = True
            specs["wca_legal"] = False
        if any(token in nameLow for token in BALL_CORE):
            specs["ball_core"] = True

    table = soup.select_one("#collapse-tab3")

    for row in table.select(".d-flex") if table else []:
        infodatalabel = row.select_one(".infodatalabel")
        infolabel = row.select_one(".infolabel")

        if not infodatalabel or not infolabel:
            continue

        label = infodatalabel.get_text()
        value = infolabel.get_text(separator=" ", strip=True)
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

        elif key in {"added", "released"}:
            specs["release_date"] = value

        elif key in {"magnets"}:
            specs["magnetic"] = value.lower() != "none"

        elif key in {"dimensions", "size"}:
            specs["size"] = format_dimensions(value)

        elif key in {"item weight", "weight"}:
            numeric_value = extract_number(value)
            if numeric_value is not None:
                specs["weight"] = numeric_value

        else:
            continue

    return specs


if __name__ == "__main__":
    run_parser_test(parse_scs)
