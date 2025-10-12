from bs4 import BeautifulSoup
import re


def format_dimensions(text: str) -> str:
    """
    Normalize a cube dimension string like:
      '68 x68 x56 mm' → '68 x 68 x 56'
      '56x56x56mm'    → '56 x 56 x 56'
      '55.5x55.5x55.5mm' → '55.5 x 55.5 x 55.5'
    """
    if not text:
        return ""

    # Replace lowercase/uppercase x or * with the proper multiplication symbol
    s = text.strip().lower().replace("*", "x").replace("×", "x")

    # Remove 'mm' or similar unit suffixes
    s = re.sub(r"\s*mm\b", "", s, flags=re.IGNORECASE)

    # Add a single space around the x sign
    s = re.sub(r"\s*x\s*", " x ", s)

    # Collapse multiple spaces
    s = re.sub(r"\s+", " ", s).strip()

    return s


def ziicube_cube_details(html):
    soup = BeautifulSoup(html, "html.parser")
    specs = {}

    preview = soup.select_one("#preview")
    img_tag = preview.select_one("img") if preview else None
    img = img_tag.attrs.get("src") if img_tag else None

    specs["Image"] = img

    table = soup.select_one("div.sku-attr")

    for row in table.select("tr") if table else []:
        tds = row.find_all("td")
        for i in range(0, len(tds), 2):
            if i + 1 >= len(tds):
                break
            name = tds[i].get_text(" ", strip=True).replace(":", "")
            value = tds[i + 1].get_text(" ", strip=True)

            match name.lower():
                case "item size":
                    name = "Size"
                    value = format_dimensions(value)
                case "net weight":
                    name = "Weight"
                    value = value.replace("g", "").strip()
                case "brand name":
                    name = "Brand"
                case _:
                    continue

            specs[name] = value

    return specs
