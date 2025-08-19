from bs4 import BeautifulSoup
from typing import Any, Dict, Optional, Tuple
import re

available_keyword = [
    "http://schema.org/InStock",
    "http://schema.org/MadeToOrder",
    "http://schema.org/OnlineOnly",
    "http://schema.org/PreOrder",
    "http://schema.org/PreSale",
]

unavailable_keyword = [
    "http://schema.org/SoldOut",
    "http://schema.org/OutOfStock",
    "http://schema.org/Discontinued",
    "http://schema.org/Reserved",
    "http://schema.org/LimitedAvailability",
    "http://schema.org/InStoreOnly",
    "http://schema.org/BackOrder",
]


def parse_cubicle(
    html: str,
) -> Tuple[Optional[float], Optional[bool], Dict[str, Any]]:
    """
    TheCubicle: price via <meta itemprop="price" content="..">
                availability via <link itemprop="availability" href="http://schema.org/...">
    """
    soup = BeautifulSoup(html, "html.parser")

    price_tag = soup.find("meta", attrs={"itemprop": "price"})
    availability_tag = soup.find("link", attrs={"itemprop": "availability"})

    price, available, availability = None, None, None

    if availability_tag:
        availability = availability_tag.get("href")

    if availability in available_keyword:
        available = True
    elif availability in unavailable_keyword:
        available = False
    else:
        available = None

    if price_tag:
        raw = price_tag.get("content")
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
            "reason": "availability+price",
            "price_node": str(price_tag) if price_tag else None,
            "availability_node": str(availability_tag) if availability_tag else None,
        },
    )
