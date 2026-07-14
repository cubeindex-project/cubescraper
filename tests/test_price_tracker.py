import pytest

from src.cubescraper.common.http import fetch_web_page
from src.cubescraper.price_tracker.parsers.atoutcubes import parse_atoutcubes
from src.cubescraper.price_tracker.parsers.gancube import parse_gancube
from src.cubescraper.price_tracker.parsers.kewbz import parse_kewbz
from src.cubescraper.price_tracker.parsers.scs import parse_scs
from src.cubescraper.price_tracker.parsers.speedcubes_co_za import (
    parse_speedcubes_co_za,
)
from src.cubescraper.price_tracker.parsers.thecubicle import parse_thecubicle

PARSER_CASES = [
    (
        "speedcubeshop",
        parse_scs,
        "https://speedcubeshop.com/products/gan-356-3x3-magnetic-maglev-core-magnets-uv-coated",
    ),
    (
        "gancube",
        parse_gancube,
        "https://www.gancube.com/products/gan356-maglev-3x3-magnetic-speed-cube",
    ),
    (
        "thecubicle",
        parse_thecubicle,
        "https://www.thecubicle.com/en-global/products/gan356-maglev-uv-3x3",
    ),
    (
        "speedcubes_co_za",
        parse_speedcubes_co_za,
        "https://www.speedcubes.co.za/products/3x3x3-gan-356-m-lite",
    ),
    (
        "kewbz",
        parse_kewbz,
        "https://kewbz.co.uk/products/gan-356-maglev-uv?_pos=1&_sid=f3509c8ab&_ss=r",
    ),
    (
        "atoutcubes",
        parse_atoutcubes,
        "https://www.atoutcubes.com/en/3x3-cubes/66950-gan-356-maglev-uv-4000000008200.html",
    ),
]


@pytest.mark.parametrize("name,parser,url", PARSER_CASES)
def test_price_parser_live(name, parser, url):
    html = fetch_web_page(url)

    if not html:
        raise Exception(f"{name}: no HTML to parse")

    result = parser(html)

    assert result.price is not None, f"{name}: price not found"
    assert result.price > 0, f"{name}: invalid price"
    assert result.availability is not None, f"{name}: availability not found"
