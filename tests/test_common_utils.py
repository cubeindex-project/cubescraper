from src.cubescraper.common.utils import extract_number, format_dimensions


def test_extract_number_handles_decimal_and_thousands_separators():
    assert extract_number("5,6 cm") == 5.6
    assert extract_number("1,234") == 1234
    assert extract_number("1.234") == 1234
    assert extract_number("1,234.56") == 1234.56
    assert extract_number("1.234,56") == 1234.56


def test_format_dimensions_handles_comma_decimals():
    assert format_dimensions("5,6 cm") == "56 x 56 x 56"
    assert format_dimensions("5,5 x 5,5 x 5,5 cm") == "55 x 55 x 55"
