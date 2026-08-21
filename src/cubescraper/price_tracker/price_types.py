from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict


@dataclass
class ParseResult:
    price: float | None
    availability: bool | None


class CubeVendorLinkPayload(TypedDict):
    id: int
    available: bool
    price: float
