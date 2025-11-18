import re, sys, os
import requests
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


def thecubicle_cube_details(html: str) -> Specs:
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
        "ball_core": None
    }

    nameLbl = soup.find("h1", {"itemprop": "name"})
    name = nameLbl.get_text(strip=True) if nameLbl else None
    specs["name"] = name

    if name is not None:
        nameLow = name.lower()

        if "maglev" in nameLow:
            specs["maglev"] = True

        if any(k in nameLow for k in ["smart", "ai"]):
            specs["smart"] = True
            specs["wca_legal"] = False
            
        if  any(k in nameLow for k in ["ball core", "ball-core"]):
            specs["ball_core"] = True

        if "uv" in nameLow:
            specs["surface_finish"] = "UV Coated"

    meta = soup.find("meta", {"itemprop": "image"})
    if meta:
        content = meta.get("content", None)  # type: ignore
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
            specs["brand"] = value

        elif key in {"type"}:
            specs["type"] = value

        elif key in {"added"}:
            specs["release_date"] = value

        elif key in {"magnets"}:
            specs["magnetic"] = value.lower() == "magnetic"

        elif key in {"dimensions"}:
            specs["size"] = value

        elif key in {"item weight"}:
            numeric_value = _extract_number(value)
            if numeric_value is not None:
                specs["weight"] = numeric_value

        else:
            continue

    return specs


if __name__ == "__main__":
    html = requests.get("https://www.thecubicle.com/en-global/products/moyu-weilong-v11-ai-3x3-8-magnet-ball-core-maglev-18th-anniversary-edition?f=versions").text

    print(thecubicle_cube_details(html))
