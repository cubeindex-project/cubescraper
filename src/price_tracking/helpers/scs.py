from bs4 import BeautifulSoup
from typing import Any, Dict, Optional, Tuple
import re


def parse_scs(
    html: str,
) -> Tuple[Optional[float], Optional[bool], Dict[str, Any]]:
    """
    SpeedCubeShop: price may be <meta itemprop="price"> or <span itemprop="price"> or .money
                   availability via input#product-add-to-cart[value="Add to cart"].
    """
    soup = BeautifulSoup(html, "html.parser")

    price_tag = (
        soup.find("meta", {"itemprop": "price"})  # meta content
        or soup.find("span", {"itemprop": "price"})
        or soup.find("span", class_="money")
    )
    availability_tag = soup.find("input", {"id": "product-add-to-cart"})

    price, available = None, None

    if availability_tag:
        val = availability_tag.get("value", "") or ""
        available = str(val).strip().lower() == "add to cart"

    if price_tag:
        raw = (
            price_tag.get("content")
            if price_tag.name == "meta"
            else price_tag.get_text()
        )
        if raw:
            raw = re.sub(r"[^\d.,]", "", str(raw)).replace(",", ".")
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
        },
    )
