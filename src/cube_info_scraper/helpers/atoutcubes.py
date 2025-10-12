from bs4 import BeautifulSoup


def atoutcubes_cube_details(html):
    soup = BeautifulSoup(html, "html.parser")

    table = soup.select_one("dl.data-sheet")

    specs = {}

    for dt in table.select("dt") if table else []:
        dd = dt.find_next_sibling("dd")

        if dd is None:
            continue

        name = dt.get_text()
        value = dd.get_text()

        specs[name] = value

    return specs
