from bs4 import BeautifulSoup
from typing import Any, Dict, Optional, Tuple

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
        price = price_tag.get("content")

    return (
        float(price),
        available,
        {"html": True, "reason": "price_tag", "price_match": price_tag},
    )
