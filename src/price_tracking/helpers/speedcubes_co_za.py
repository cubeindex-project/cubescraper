from bs4 import BeautifulSoup
from typing import Any, Dict, Optional, Tuple
import re


def parse_speedcubes_co_za(
    html: str,
) -> Tuple[Optional[float], Optional[bool], Dict[str, Any]]:
    """
    speedcubes.co.za: price in .product-price--original; add-to-cart disabled => OOS.
    """
    soup = BeautifulSoup(html, "html.parser")

    price_tag = soup.find("span", class_="product-price--original")
    availability_tag = soup.find("button", class_="add-to-cart")

    price, available = None, None

    if availability_tag:
        available = not availability_tag.has_attr("disabled")

    if price_tag:
        raw = price_tag.get_text()
        if raw:
            raw = re.sub(r"[^\d.,]", "", raw).replace(",", ".")
            try:
                price = float(raw)
            except Exception:
                price = None

    return (
        price,
        available,
        {
            "html": True,
            "reason": "price_tag",
            "price_node": str(price_tag) if price_tag else None,
            "availability_node": str(availability_tag) if availability_tag else None,
        },
    )
