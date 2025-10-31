import re, sys, os
from bs4 import BeautifulSoup

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)
from src.cube_info_scraper.fetch_cube_info import Specs


def _extract_number(value: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)", value)
    if not match:
        return None
    return float(match.group(1))


def scs_cube_details(html: str) -> Specs:
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
        "source": "scs"
    }

    img = soup.select_one("img[id^='product-featured-image']")

    if img and img.get("src"):
        image_url = img["src"]
        if isinstance(image_url, str) and image_url.startswith("//"):
            specs["image_url"] = "https:" + image_url
        elif isinstance(image_url, str):
            specs["image_url"] = image_url

    nameLbl = soup.select_one("h1.product-title")
    name = nameLbl.get_text(strip=True) if nameLbl else None
    specs["name"] = name

    if name is not None:
        nameLow = name.lower()

        if "uv coated" in nameLow:
            specs["surface_finish"] = "UV Coated"
        if any(token in nameLow for token in ["limited", "anniversary"]):
            specs["version_type"] = "Limited"
        if "magnetic" in nameLow:
            specs["magnetic"] = True
        if "maglev" in nameLow:
            specs["maglev"] = True
        if "smart" in nameLow:
            specs["smart"] = True
            specs["wca_legal"] = False
        if any(token in nameLow for token in ["ball core", "ball-core"]):
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
            specs["brand"] = value

        elif key in {"type"}:
            specs["type"] = value

        elif key in {"added", "released"}:
            specs["release_date"] = value

        elif key in {"magnets"}:
            specs["magnetic"] = value.lower() != "none"

        elif key in {"dimensions", "size"}:
            specs["size"] = value

        elif key in {"item weight", "weight"}:
            numeric_value = _extract_number(value)
            if numeric_value is not None:
                specs["weight"] = numeric_value

        else:
            continue

    return specs


if __name__ == "__main__":
    html = open(
        "C:/Users/ilans/Documents/GitHub/cubescraper/.debug/SpeedCubeShop/gan-15-maglev-uv-10th-anniversary-edition.html",
        "r",
        encoding="utf-8",
    ).read()
    print(scs_cube_details(html))
