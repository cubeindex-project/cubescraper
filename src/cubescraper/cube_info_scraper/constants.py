from typing import Dict

from cubescraper.cube_info_scraper.cube_info_types import CubeSurfaceFinish

SUPPORTED_VENDORS: Dict[str, str] = {
    "thecubicle.com": "cubescraper.cube_info_scraper.parsers.thecubicle:parse_thecubicle",
    "speedcubeshop.com": "cubescraper.cube_info_scraper.parsers.scs:parse_scs",
}

BALL_CORE = ["ball core", "ball-core"]
SMART = ["smart", "ai"]
LIMITED = ["limited", "anniversary"]
TRANSPARENT = ["transparent"]
SURFACE_FINISH: Dict[str, CubeSurfaceFinish] = {
    "uv": "UV Coated",
    "frosted": "Frosted",
    "glossy": "Glossy",
    "sculpted": "Sculpted",
}

FUZZY_OVERRIDES: dict[str, str] = {
    "8x8-21x21 Cubes": "8x8x8",
    "7x7 Speed Cubes": "7x7x7",
    "6x6 Speed Cubes": "6x6x6",
    "5x5 Speed Cubes": "5x5x5",
    "4x4 Speed Cubes": "4x4x4",
    "3x3 Speed Cubes": "3x3x3",
    "2x2 Speed Cubes": "2x2x2",
}
