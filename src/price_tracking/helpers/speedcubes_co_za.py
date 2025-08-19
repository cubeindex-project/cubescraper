from bs4 import BeautifulSoup
from typing import Any, Dict, Optional, Tuple


def parse_speedcubes_co_za(
    html: str,
) -> Tuple[Optional[float], Optional[bool], Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")

    price_tag = soup.find("span", class_="product-price--original")
    availability_tag = soup.find("button", class_="add-to-cart")

    price, available = None, None

    if availability_tag.has_attr("disabled"):
        available = False
    elif not availability_tag.has_attr("disabled"):
        available = True
    else:
        available = None

    if price_tag:
        price = (price_tag.get_text()).replace("R", "").strip()

    return (
        float(price),
        available,
        {"html": True, "reason": "price_tag", "price_match": price_tag},
    )
