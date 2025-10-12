from bs4 import BeautifulSoup


def scs_cube_details(html):
    soup = BeautifulSoup(html, "html.parser")

    table = soup.select_one("#collapse-tab3")

    specs = {}

    for row in table.select(".d-flex") if table else []:
        infodatalabel = row.select_one(".infodatalabel")
        infolabel = row.select_one(".infolabel")

        if not infodatalabel or not infolabel:
            continue

        name = infodatalabel.get_text()
        value = infolabel.get_text(separator=" ", strip=True)

        specs[name] = value

    return specs
