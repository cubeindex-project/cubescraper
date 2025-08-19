from bs4 import BeautifulSoup
from typing import Any, Dict, Optional, Tuple


def parse_scs(
    html: str,
) -> Tuple[Optional[float], Optional[bool], Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")

    price_tag = soup.find("span", {"itemprop": "price"})
    availability_tag = soup.find("input", {"id": "product-add-to-cart"})

    price, available = None, None

    if availability_tag:
        if availability_tag["value"] == "Add to cart":
            available = True
        elif availability_tag["value"] != "Add to cart":
            available = False
        else:
            available = None

    if price_tag:
        price = (
            (price_tag.find("span", class_="money").get_text()).replace("$", "").strip()
        )

    return (
        float(price),
        available,
        {"html": True, "reason": "price_tag", "price_match": price_tag},
    )
