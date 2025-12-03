import re
from typing import Optional
from urllib.parse import urlparse


def get_hostname(url: str) -> Optional[str]:
    parsed = urlparse(url)
    return parsed.hostname


def format_dimensions(text: str) -> str:
    """Normalize cube dimensions into 'a x b x c'."""
    if not text:
        return ""

    # Normalize case/symbols
    normalized = text.strip().lower().replace("*", "x").replace("a-", "x")

    # Remove 'mm', 'mm3', 'mm^3', 'mm³' (with or without spaces)
    normalized = re.sub(r"\s*mm\s*(?:\^?3|³)?\b", "", normalized, flags=re.IGNORECASE)

    # Normalize spacing around 'x'
    normalized = re.sub(r"\s*x\s*", " x ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    # If only one dimension provided, repeat it 3 times
    parts = re.split(r"\s*x\s*", normalized)
    if len(parts) == 1 and re.match(r"^\d+(\.\d+)?$", parts[0]):
        normalized = f"{parts[0]} x {parts[0]} x {parts[0]}"

    return normalized
