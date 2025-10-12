from bs4 import BeautifulSoup

html = open(
    "C:/Users/ilans/Documents/GitHub/cubescraper/.debug/TheCubicle/dayan-guhong-pro-m-54mm-maglev.html",
    "r",
    encoding="utf-8",
).read()


def the_cubicle_cube_details(html) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("table.w-full.border-collapse.border.border-gray-200")
    specs = {}
    for tr in table.select("tr") if table else []:
        th = tr.find("th")
        td = tr.find("td")
        if not th or not td:
            continue

        label = th.get_text(strip=True)
        val = td.get_text(separator=" ", strip=True)

        match label.lower():
            case "manufacturer":
                label = "Brand"
            case "type":
                pass
            case "added":
                label = "Released"
            case "magnets":
                label = "Magnetic"
                if val == "Magnetic":
                    val = True
                else:
                    val = False
            case "item weight":
                label = "Weight"
                val = val.replace("g", "").strip()
            case _:
                continue

        specs[label] = val

    return specs


print(the_cubicle_cube_details(html))
