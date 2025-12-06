from typing import Dict

SUPPORTED_VENDORS: Dict[str, str] = {
    "thecubicle.com": "cubescraper.price_tracker.parsers.thecubicle:parse_thecubicle",
    "gancube.com": "cubescraper.price_tracker.parsers.gancube:parse_gancube",
    "speedcubeshop.com": "cubescraper.price_tracker.parsers.scs:parse_scs",
    "speedcubes.co.za": "cubescraper.price_tracker.parsers.speedcubes_co_za:parse_speedcubes_co_za",
}
