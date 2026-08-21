from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TypedDict


@dataclass
class ParseResult:
    price: Optional[float]
    availability: Optional[bool]


class CubeVendorLinkPayload(TypedDict):
    id: int
    available: bool
    price: float
