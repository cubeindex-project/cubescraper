import pytest

from src.cubescraper.common.http import fetch_web_page
from src.cubescraper.cube_info_scraper.parser import parse_cube_details

PARSER_CASES = [
    (
        "speedcubeshop",
        "https://speedcubeshop.com/products/gan-356-3x3-magnetic-maglev-core-magnets-uv-coated",
        [
            "name",
            "image_url",
            "magnetic",
            "maglev",
            "surface_finish",
        ],
    ),
    (
        "thecubicle",
        "https://www.thecubicle.com/en-global/products/gan356-maglev-uv-3x3",
        [
            "name",
            "maglev",
            "surface_finish",
            "image_url",
            "brand",
            "type",
            "release_date",
            "size",
            "magnetic",
            "weight",
            "wca_legal",
        ],
    ),
]


@pytest.mark.live
@pytest.mark.parametrize("vendor,url,expected", PARSER_CASES)
def test_cube_info_parsers(vendor, url, expected):
    html = fetch_web_page(url)
    assert html, f"{vendor}: no HTML to parse"

    result = parse_cube_details(html, url)

    missing = [key for key in expected if key not in result]
    assert not missing, f"{vendor}: missing fields {missing}. Got: {result}"
