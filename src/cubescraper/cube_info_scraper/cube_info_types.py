from typing import Literal, Optional, TypedDict

CubeVersionType = Literal["Base", "Trim", "Limited"]
CubeSurfaceFinish = Optional[Literal["Frosted", "UV Coated", "Glossy", "Sculpted"]]


class ParserResult(TypedDict, total=False):
    brand: str
    image_url: str
    type: str
    discontinued: bool
    release_date: str
    weight: float
    version_type: CubeVersionType
    surface_finish: CubeSurfaceFinish
    size: str
    magnetic: bool
    maglev: bool
    smart: bool
    stickered: bool
    wca_legal: bool
    modded: bool
    ball_core: bool
