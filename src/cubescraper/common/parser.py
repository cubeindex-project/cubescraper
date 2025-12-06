import re
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

NUMBER_REGEX = re.compile(
    r"(\d{1,3}(?:[ ,.\u00A0]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)",
    re.VERBOSE,
)


def get_hostname(url: str) -> Optional[str]:
    parsed = urlparse(url)
    return parsed.hostname


def format_dimensions(text: str) -> str:
    """Normalize cube dimensions into 'a x b x c'."""
    if not text:
        return ""

    normalized = text.strip().lower().replace("*", "x").replace("a-", "x")
    normalized = re.sub(r"\s*mm\s*(?:\^?3|³)?\b", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\s*x\s*", " x ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    parts = re.split(r"\s*x\s*", normalized)
    if len(parts) == 1 and re.match(r"^\d+(\.\d+)?$", parts[0]):
        normalized = f"{parts[0]} x {parts[0]} x {parts[0]}"

    return normalized


def extract_number(value: str) -> float | None:
    match = re.search(NUMBER_REGEX, value)
    if not match:
        return None

    raw = match.group(1)

    cleaned = (
        raw.replace("\u00a0", "")  # remove non-breaking spaces
        .replace(" ", "")  # remove normal spaces
        .replace(",", ".")  # convert , decimal to .
    )

    parts = cleaned.split(".")
    if len(parts) > 2:
        cleaned = "".join(parts[:-1]) + "." + parts[-1]

    return float(cleaned)


def soupify(html: str):
    return BeautifulSoup(html, "lxml")
