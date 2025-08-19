from bs4 import BeautifulSoup
from typing import Any, Dict, Optional, Tuple
import re


def parse_gancube(
    html: str,
) -> Tuple[Optional[float], Optional[bool], Dict[str, Any]]:
    """
    GANCube (Shopify theme): price is in .price-item--sale/--regular or <meta itemprop="price">
                             availability inferred from product-form submit button disabled state.
    """
    soup = BeautifulSoup(html, "html.parser")

    price_tag = (
        soup.find("span", class_="price-item--sale")
        or soup.find("span", class_="price-item--regular")
        or soup.find("meta", attrs={"itemprop": "price"})
    )
    availability_tag = soup.find("button", class_="product-form__submit")

    price, available = None, None

    if availability_tag:
        available = not availability_tag.has_attr("disabled")

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
