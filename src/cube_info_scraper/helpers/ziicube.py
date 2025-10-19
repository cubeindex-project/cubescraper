import re, sys, os
from bs4 import BeautifulSoup
from typing import cast

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)
from src.cube_info_scraper.fetch_cube_info import Specs

html = open(
    "C:/Users/ilans/Documents/GitHub/cubescraper/.debug/ziicube-gan12ui.html",
    "r",
    encoding="utf-8",
).read()


def _extract_first_number(value: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)", value)
    if not match:
        return None
    return float(match.group(1))


def ziicube_cube_details(html: str) -> Specs:
    soup = BeautifulSoup(html, "html.parser")
    specs: Specs = {
        "name": None,
        "brand": None,
        "image_url": None,
        "type": None,
        "discontinued": None,
        "release_date": None,
        "weight": None,
        "version_type": None,
        "surface_finish": None,
        "size": None,
        "magnetic": None,
        "maglev": None,
        "smart": None,
        "stickered": None,
        "wca_legal": None,
        "modded": None,
        "ball_core": None,
    }

    preview = soup.select_one("#preview")
    img_tag = preview.select_one("img") if preview else None
    img = img_tag.attrs.get("src") if img_tag else None

    specs["image_url"] = str(img)

    table = soup.select_one("div.sku-attr")

    for row in table.select("tr") if table else []:
        tds = row.find_all("td")
        for i in range(0, len(tds), 2):
            if i + 1 >= len(tds):
                break

            name = tds[i].get_text(" ", strip=True).replace(":", "")
            value = tds[i + 1].get_text(" ", strip=True)
            key = name.lower()

            if key in {"item size", "cube size", "dimensions"}:
                specs["size"] = value

            if key in {"type"}:
                specs["type"] = value

            elif key in {"net weight", "weight"}:
                weight_value = _extract_first_number(value)
                if weight_value is not None:
                    specs["weight"] = weight_value

            elif key in {"brand name", "brand"}:
                specs["brand"] = value

            elif key in {"magnets", "magnetic"}:
                specs["magnetic"] = value.lower() in {"magnetic", "yes", "true"}

            elif key in {"release date", "released", "launch date"}:
                specs["release_date"] = value

            elif key in {"cube type", "type"}:
                specs["type"] = value

    return specs


print(ziicube_cube_details(html))
