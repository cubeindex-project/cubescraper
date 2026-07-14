from typing import TypedDict

from cubescraper.common.database_types import (
    PublicCubeSurfaceFinishes,
    PublicCubeVersionType,
)


class CubeInfoParserResult(TypedDict, total=False):
    name: str
    brand: str
    image_url: str

    type: str
    discontinued: bool
    release_date: str
    weight: float
    version_type: PublicCubeVersionType
    surface_finish: PublicCubeSurfaceFinishes
    size: str

    magnetic: bool
    maglev: bool
    smart: bool
    stickered: bool
    wca_legal: bool
    modded: bool
    ball_core: bool
