from bs4 import BeautifulSoup
from typing import Any, Dict, Optional, Tuple

def parse_gancube(
    html: str,
) -> Tuple[Optional[float], Optional[bool], Optional[str], Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")

    price_tag = soup.find("span", class_="price-item--sale")
    availability_tag = soup.find("button", class_="product-form__submit")

    price, available = None, None

    if availability_tag:
        if availability_tag.has_attr("disabled"):
            available = False
        elif not availability_tag.has_attr("disabled"):
            available = True
        else:
            available = None

    if price_tag:
        price = str(price_tag.get_text()).replace("$", "")

    return (
        float(price),
        available,
        "USD",
        {"html": True, "reason": "price_tag", "price_match": price_tag},
    )
