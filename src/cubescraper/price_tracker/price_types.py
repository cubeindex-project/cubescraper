from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, TypedDict


class CubeVendorLink(TypedDict):
    vendor_name: str
    url: str
    created_at: datetime
    id: int
    updated_at: datetime
    available: bool
    cube_slug: str
    price: float
    last_modified: datetime


@dataclass
class ParseResult:
    price: Optional[float]
    availability: Optional[bool]


class CubeVendorLinkPayload(TypedDict):
    id: int
    available: bool
    price: float
