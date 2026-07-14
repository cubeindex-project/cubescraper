from typing import Dict

from cubescraper.common.database_types import PublicCubeSurfaceFinishes

BALL_CORE = ["ball core", "ball-core"]
SMART = ["smart", "ai"]
LIMITED = ["limited", "anniversary"]
TRANSPARENT = ["transparent"]
SURFACE_FINISH: Dict[str, PublicCubeSurfaceFinishes] = {
    "uv coated": "UV Coated",
    "uv": "UV Coated",
    "frosted": "Frosted",
    "glossy": "Glossy",
    "sculpted": "Sculpted",
}

FUZZY_OVERRIDES: dict[str, str] = {
    "8x8-21x21 cubes": "8x8x8",
    "7x7 speed cubes": "7x7x7",
    "6x6 speed cubes": "6x6x6",
    "5x5 speed cubes": "5x5x5",
    "4x4 speed cubes": "4x4x4",
    "3x3 speed cubes": "3x3x3",
    "2x2 speed cubes": "2x2x2",
    "3x3 magnetic speed cube": "3x3x3",
}
"""A dictionary of values to override the fuzzy search."""

WCA_LEGAL_CUBE_TYPES = [
    "2x2x2",
    "3x3x3",
    "4x4x4",
    "5x5x5",
    "6x6x6",
    "7x7x7",
    "Megaminx",
    "Pyraminx",
    "Skewb",
    "Square-1",
    "FTO",
]
