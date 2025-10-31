import argparse
import logging
import os
import re
import sys
import unicodedata

import requests
from datetime import date, datetime
from typing import (
    Callable,
    Literal,
    Optional,
    TypedDict,
    Tuple,
    List,
    Dict,
    Any,
    Iterable,
)
from collections import Counter, defaultdict
from urllib.parse import urlparse
from rapidfuzz import fuzz
from slugify import slugify
from difflib import get_close_matches

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.common.supabaseClient import supabase
from src.price_tracking.fetch_cube_price import process_link

parser = argparse.ArgumentParser(
    "fetch_cube_info",
    description="Fetch job links and cube details from them to insert into the database.",
)


# Require positive integers for --limit
def positive_int(value: str) -> int:
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("limit must be > 0")
    return ivalue


parser.add_argument("--debug", action="store_true", help="Enable DEBUG logs.")
parser.add_argument(
    "--limit",
    type=positive_int,
    default=100,
    help="Only process the first N jobs (> 0).",
)
parser.add_argument(
    "--force",
    action="store_true",
    help="Process jobs regardless of status.",
)

args = parser.parse_args()
debug: bool = args.debug
limit: int = args.limit


class ConsoleFormatter(logging.Formatter):
    """Console-friendly formatter with optional ANSI colors and aligned columns."""

    RESET = "\033[0m"
    LEVEL_STYLES = {
        logging.DEBUG: ("DEBUG", "\033[36m"),
        logging.INFO: ("INFO", "\033[32m"),
        logging.WARNING: ("WARNING", "\033[33m"),
        logging.ERROR: ("ERROR", "\033[31m"),
        logging.CRITICAL: ("CRITICAL", "\033[41m"),
    }

    def __init__(self, use_color: bool) -> None:
        super().__init__(fmt="%(levelname)s | %(message)s")
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        original_levelname = record.levelname
        record.short_name = record.name.rsplit(".", 1)[-1]

        label, color = self.LEVEL_STYLES.get(record.levelno, (record.levelname, ""))
        padded_label = label.ljust(8)

        if self.use_color and color:
            record.levelname = f"{color}{padded_label}{self.RESET}"
        else:
            record.levelname = padded_label

        try:
            return super().format(record)
        finally:
            record.levelname = original_levelname


def configure_logger(debug_mode: bool) -> logging.Logger:
    """Create a console logger with cleaner formatting."""
    level = logging.DEBUG if debug_mode else logging.INFO
    parent_logger = logging.getLogger("cube_info_scraper")
    parent_logger.setLevel(level)
    parent_logger.handlers.clear()
    parent_logger.propagate = False

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    stream = console_handler.stream
    use_color = hasattr(stream, "isatty") and stream.isatty()
    console_handler.setFormatter(ConsoleFormatter(use_color=use_color))
    parent_logger.addHandler(console_handler)

    child_logger = parent_logger.getChild("fetch_cube_info")

    if debug_mode:
        child_logger.debug("Debug logging enabled.")
    return child_logger


logger = configure_logger(debug)

CubeVersionType = Literal["Base", "Trim", "Limited"]
CubeSurfaceFinish = Optional[Literal["Frosted", "UV Coated", "Glossy", "Sculpted"]]
CubeSubType = Optional[
    Literal[
        "NxNxN",
        "Square-N",
        "Minx",
        "Shape-Shifting",
        "Cuboid",
        "Non-Twisty",
        "Corner-Turning",
        "Gear",
        "Other",
    ]
]


class Specs(TypedDict):
    name: Optional[str]
    brand: Optional[str]
    image_url: Optional[str]
    type: Optional[str]
    discontinued: Optional[bool]
    release_date: Optional[str]
    weight: Optional[float]
    version_type: Optional[CubeVersionType]
    surface_finish: Optional[CubeSurfaceFinish]
    size: Optional[str]
    magnetic: Optional[bool]
    maglev: Optional[bool]
    smart: Optional[bool]
    stickered: Optional[bool]
    wca_legal: Optional[bool]
    modded: Optional[bool]
    ball_core: Optional[bool]
    source: str


class CubeDBSchema(TypedDict):
    brand: str
    image_url: str
    model: str
    slug: str
    type: str
    discontinued: bool
    release_date: Optional[date]
    series: str
    sub_type: CubeSubType
    weight: float
    related_to: Optional[str]
    version_type: CubeVersionType
    version_name: str
    surface_finish: CubeSurfaceFinish
    size: Optional[str]
    submitted_by_id: str


class CubeFeaturesDBSchema(TypedDict):
    cube: str
    feature: str

class VendorLinkCandidate(TypedDict):
    vendor_name: str
    url: str
    price: Optional[float]
    available: Optional[bool]


class VendorLinkInsertPayload(TypedDict, total=False):
    vendor_name: str
    url: str
    cube_slug: str
    price: float
    available: bool


SUPPORTED_STORES = {"thecubicle.com", "speedcubeshop.com"}
VENDOR_DOMAIN_TO_NAME = {
    "thecubicle.com": "TheCubicle",
    "speedcubeshop.com": "SpeedCubeShop",
    "gancube.com": "GANCUBE",
    "speedcubes.co.za": "Speedcubes.co.za",
}
REQUEST_TIMEOUT_SECONDS = 12.0
SIMILARITY_THRESHOLD = 0
USER_AGENT_HEADERS = {
    "User-Agent": "CubeIndexBot/1.0 (+support@cubeindex.app)",
    "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
}


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


def fetch_jobs(limit: int = 100) -> List[Dict[str, Any]]:
    logger.info("Fetching next jobs...")

    try:
        query = (
            supabase.table("cube_scrap_runs").select("id, user_id").order("created_at")
        )

        if not args.force:
            query = query.eq("status", "queued")

        jobs = query.limit(limit).execute()
    except Exception:
        logger.exception("Error fetching next jobs from Supabase.")
        raise

    if not jobs:
        logger.info("No jobs found!")
        sys.exit(1)

    return jobs.data


def fetch_job_links(job_id: str) -> list[str]:
    logger.info("Fetching job links for job_id=%s...", job_id)

    raw_job_links = (
        supabase.table("cube_scrap_runs_url")
        .select("normalized_url")
        .order("created_at")
        .eq("run_id", job_id)
        .execute()
    )

    job_links = [
        row.get("normalized_url")
        for row in raw_job_links.data
        if row.get("normalized_url")
    ]

    if not job_links:
        logger.error("No job links found for job_id=%s!", job_id)
        sys.exit(1)

    logger.info("%d links fetched.", len(job_links))
    logger.debug("Processing job links...")
    return job_links  # type: ignore


def _resolve_parser(hostname: str) -> Optional[Callable[[str], Specs]]:
    if hostname.endswith("thecubicle.com"):
        from src.cube_info_scraper.helpers.thecubicle import thecubicle_cube_details

        return thecubicle_cube_details
    if hostname.endswith("speedcubeshop.com"):
        from src.cube_info_scraper.helpers.scs import scs_cube_details

        return scs_cube_details
    return None


def fetch_store_cube_details(job_links: list[str]) -> list[Specs]:
    store_cube_details: list[Specs] = []

    for index, link in enumerate(job_links, start=1):
        parsed_link = urlparse(link)
        hostname = (parsed_link.hostname or "").lower()

        if not any(hostname.endswith(domain) for domain in SUPPORTED_STORES):
            logger.warning("Skipping unsupported store: %s", parsed_link.hostname)
            continue

        parser = _resolve_parser(hostname)
        if parser is None:
            logger.warning("No parser implemented for %s", parsed_link.hostname)
            continue

        try:
            response = requests.get(
                link, headers=USER_AGENT_HEADERS, timeout=REQUEST_TIMEOUT_SECONDS
            )
        except requests.RequestException as exc:
            logger.error("Failed to fetch %s: %s", link, exc)
            continue

        store_cube_details.append(parser(response.text))
        logger.debug("Link %s/%s processed (%s).", index, len(job_links), link)

    logger.info("All links processed.")
    return store_cube_details


def verify_cube_details(store_cube_details: list[Specs]) -> None:
    logger.info("Verifying data consistency across links...")

    verif_score = 0
    pairs_checked = 0

    for previous, current in zip(store_cube_details, store_cube_details[1:]):
        name_a, name_b = previous.get("name", ""), current.get("name", "")
        brand_a, brand_b = previous.get("brand", ""), current.get("brand", "")
        type_a, type_b = previous.get("type", ""), current.get("type", "")

        if not name_a or not name_b:
            logger.warning("Missing name in one of the entries, skipping comparison.")
            continue

        if not brand_a or not brand_b:
            logger.warning("Missing brand in one of the entries, skipping comparison.")
            continue

        if not type_a or not type_b:
            logger.warning("Missing type in one of the entries, skipping comparison.")
            continue

        name_match_percent = fuzz.token_sort_ratio(name_a.lower(), name_b.lower())
        brand_match_percent = fuzz.token_sort_ratio(brand_a.lower(), brand_b.lower())
        type_match_percent = fuzz.token_sort_ratio(type_a.lower(), type_b.lower())

        pairs_checked += 1
        if (
            name_match_percent >= SIMILARITY_THRESHOLD
            and brand_match_percent >= SIMILARITY_THRESHOLD
            and type_match_percent >= SIMILARITY_THRESHOLD
        ):
            verif_score += 1

    if verif_score != pairs_checked:
        logger.error(
            "Only %s/%s pairs matched (threshold %s%%).",
            verif_score,
            pairs_checked,
            SIMILARITY_THRESHOLD,
        )
        sys.exit(1)

    logger.info("All links match the same cube.")


Resolver = Callable[[list[Any]], Any]


def _first_non_none(values: Iterable[Any]) -> Any:
    for v in values:
        if v is not None and v != "":
            return v
    return None


def _most_common(values: Iterable[Any]) -> Any:
    vals = [v for v in values if v is not None and v != ""]
    return Counter(vals).most_common(1)[0][0] if vals else None


def _to_date(v: Any) -> Optional[date]:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, str) and v.strip():
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(v, fmt).date()
            except ValueError:
                pass
    return None


def _resolve_release_date(values: List[Any]) -> Optional[str]:
    dates = [_to_date(v) for v in values]
    dates = [d for d in dates if d is not None]
    return min(dates).isoformat() if dates else None


def _resolve_image(values: list[Any]) -> Optional[str]:
    # first non-empty URL wins; fall back to last non-empty if you prefer
    return _first_non_none(values)


VALID_TYPES = {
    "Square-1",
    "3x3x3",
    "2x2x2",
    "4x4x4",
    "5x5x5",
    "6x6x6",
    "7x7x7",
    "8x8x8",
    "9x9x9",
    "10x10x10",
    "Megaminx",
    "Gigaminx",
    "Kilominx",
    "Master Kilominx",
    "Teraminx",
    "Petaminx",
    "Pyraminx",
    "Skewb",
    "Mirror",
    "Gear Cube",
    "Shape Mod",
    "Clock",
    "1x3x3",
    "1x1x2",
    "Other",
}

ALLOWED_TYPES = [
    "Square-1",
    "3x3x3",
    "2x2x2",
    "4x4x4",
    "5x5x5",
    "6x6x6",
    "7x7x7",
    "8x8x8",
    "9x9x9",
    "10x10x10",
    "Megaminx",
    "Pyraminx",
    "Gigaminx",
    "Kilominx",
    "Master Kilominx",
    "Teraminx",
    "Petaminx",
    "Skewb",
    "Mirror",
    "Gear Cube",
    "Shape Mod",
    "Clock",
    "1x3x3",
    "1x1x2",
    "Other",
]
_CANON_LC = {c.lower(): c for c in ALLOWED_TYPES}

ALIASES = {
    "sq1": "Square-1",
    "square1": "Square-1",
    "square one": "Square-1",
    "3x3": "3x3x3",
    "2x2": "2x2x2",
    "4x4": "4x4x4",
    "5x5": "5x5x5",
    "6x6": "6x6x6",
    "7x7": "7x7x7",
    "8x8": "8x8x8",
    "9x9": "9x9x9",
    "10x10": "10x10x10",
    "mirror cube": "Mirror",
    "gear": "Gear Cube",
    "clock cube": "Clock",
    "megaminx cube": "Megaminx",
    "pyraminx cube": "Pyraminx",
    "skewb cube": "Skewb",
}

# 3x3, 3x3x3, 3×3×3, "3 x 3", with optional "cube"
_NXN = re.compile(r"^\s*(\d{1,2})\s*[x×*]\s*\1(?:\s*[x×*]\s*\1)?\s*(?:cube)?\s*$", re.I)


def canonicalize_type(raw: Optional[str], cutoff: float = 0.74) -> str:
    if not raw or not str(raw).strip():
        return "Other"
    s = re.sub(r"\s+", " ", str(raw).strip().lower())

    # NxNxN normalize → "NxNxN"
    m = _NXN.match(s)
    if m:
        n = m.group(1)
        nxn = f"{n}x{n}x{n}"
        if nxn in _CANON_LC:  # e.g., 3x3→3x3x3
            return _CANON_LC[nxn]

    # alias or exact canonical
    if s in ALIASES:
        return ALIASES[s]
    if s in _CANON_LC:
        return _CANON_LC[s]

    # fuzzy over known terms (canonical + aliases)
    corpus = list(_CANON_LC.keys()) + list(ALIASES.keys())
    match = get_close_matches(s, corpus, n=1, cutoff=cutoff)
    if match:
        k = match[0]
        return _CANON_LC.get(k, ALIASES.get(k, "Other"))

    return "Other"


def _resolve_type(values: Iterable[Optional[str]], cutoff: float = 0.74) -> str:
    canon = [canonicalize_type(v, cutoff) for v in values if v and str(v).strip()]
    if not canon:
        return "Other"
    top = Counter(canon).most_common(1)[0][0]
    return top


def _resolve_bool(values: List[Any]) -> Optional[bool]:
    seen_true = False
    seen_false = False
    for v in values:
        if v == True:
            seen_true = True
        elif v == False:
            seen_false = True

    if seen_true:
        return True
    if seen_false:
        return False
    return None


def _resolve_numeric(values: list[Any]) -> Optional[float]:
    nums: list[float] = []
    for v in values:
        if v is None or v == "":
            continue
        try:
            nums.append(float(v))
        except (TypeError, ValueError):
            pass
    # Pick most common numeric, or first, or median—your choice:
    return _most_common(nums) if nums else None


def _resolve_string(values: list[Any]) -> Optional[str]:
    vals = [str(v) for v in values if v not in (None, "")]
    if not vals:
        return None
    counts = Counter(vals).most_common()
    top_count = counts[0][1]
    candidates = [v for v, c in counts if c == top_count]
    return candidates[0]  # first most-common


RULES: dict[str, Resolver] = {
    "release_date": _resolve_release_date,
    "image_url": _resolve_image,
    # booleans
    "magnetic": _resolve_bool,
    "maglev": _resolve_bool,
    "smart": _resolve_bool,
    "stickered": _resolve_bool,
    "wca_legal": _resolve_bool,
    "modded": _resolve_bool,
    "ball_core": _resolve_bool,
    # numerics
    "weight": _resolve_numeric,
    "size": _resolve_numeric,
    # strings (explicit if you want, else default below handles)
    # "name": _resolve_string,
    # "brand": _resolve_string,
    "type": lambda vals: _resolve_type(vals, cutoff=0.74),
    # "version_type": _resolve_string,
    # "surface_finish": _resolve_string,
    # "discontinued": _resolve_bool,  # if this is actually boolean
}


ALL_KEYS = [
    "name",
    "brand",
    "image_url",
    "type",
    "discontinued",
    "release_date",
    "weight",
    "version_type",
    "surface_finish",
    "size",
    "magnetic",
    "maglev",
    "smart",
    "stickered",
    "wca_legal",
    "modded",
    "ball_core",
]


def merge_cube_details(rows: list[Specs]) -> Specs:
    # 1) collect all candidate values per key (preserve input order for tie-breakers)
    bucket: dict[str, list[Any]] = defaultdict(list)
    for row in rows:
        for k in ALL_KEYS:
            bucket[k].append(row.get(k))

    # 2) resolve each key with the appropriate rule
    merged: Specs = {
        "name": None,
        "brand": None,
        "image_url": None,
        "type": None,
        "discontinued": None,
        "release_date": None,
        "weight": None,
        "version_type": None,
        "surface_finish": None,
        "size": None,
        "magnetic": None,
        "maglev": None,
        "smart": None,
        "stickered": None,
        "wca_legal": None,
        "modded": None,
        "ball_core": None,
        "source": "",
    }

    for k in ALL_KEYS:
        values = bucket.get(k, [])
        resolver = RULES.get(k)
        if resolver is None:
            # default: prefer most common non-empty string; else first non-none for other types
            # You can specialize further if needed.
            merged[k] = (
                _resolve_string(values)
                if any(isinstance(v, str) for v in values if v is not None)
                else _first_non_none(values)
            )
        else:
            merged[k] = resolver(values)

    return merged


def _resolve_vendor_name(url: str) -> Optional[str]:
    hostname = (urlparse(url).hostname or "").lower()
    for domain, vendor_name in VENDOR_DOMAIN_TO_NAME.items():
        if hostname.endswith(domain):
            return vendor_name
    return None


def prepare_vendor_links(job_links: list[str]) -> List[VendorLinkCandidate]:
    vendor_links: List[VendorLinkCandidate] = []
    for link in job_links:
        vendor_name = _resolve_vendor_name(link)
        if not vendor_name:
            logger.debug("Skipping vendor link for unsupported host: %s", link)
            continue

        try:
            result = process_link(link, force=True)
        except Exception as exc:  # pragma: no cover - network errors depend on env
            logger.warning(
                "Failed to fetch vendor details for %s (%s). Falling back to placeholders.",
                link,
                exc,
            )
            vendor_links.append(
                {
                    "vendor_name": vendor_name,
                    "url": link,
                    "price": None,
                    "available": None,
                }
            )
            continue

        price = result.price if result.outcome != "error" else None
        available = result.available if result.outcome != "error" else None
        vendor_links.append(
            {
                "vendor_name": vendor_name,
                "url": link,
                "price": price,
                "available": available,
            }
        )

    return vendor_links


def parse_series_and_model(raw_name: str, raw_brand: str) -> Tuple[str, str, str]:
    """
    Returns (series, model, version_name)
    """
    if not raw_name:
        return (raw_brand or "", "", "")

    # inline helpers (kept inside to satisfy "one function")
    COLOR_WORDS = {
        "black",
        "white",
        "blue",
        "green",
        "purple",
        "lilac",
        "gold",
        "golden",
        "silver",
        "emeraldox",
        "newblack",
        "new black",
        "matte",
    }
    VERSION_PHRASES = {
        # editions / events
        "special edition",
        "spirit pearl",
        "10th anniversary edition",
        "lunar new year edition",
        "brainstorm voyage edition",
        # features / materials / extras
        "uv",
        "uv coated",
        "enhanced",
        "pioneer",
        "flagship",
        "max",
        "fx",
        "ferrocore",
        "robot stand",
        "magnetic core",
        "core magnets",
        "ball-core",
        "20 magnet ball-core",
        "8-magnet-ball-core",
        "20-magnet-ball-core",
        "green internals",
    }
    MODEL_FEATURE_TOKENS = {
        "m",
        "maglev",
        "lite",
        "pro",
        "leap",
        "air",
        "duo",
        "carry",
        "carry e",
        "carry 2",
        "s",
        "me",
        "me v2",
        "ai",
    }
    UV_TIGHT_IN_MODEL = True

    SIZE_NxN = re.compile(r"^\d+\s*[x×]\s*\d+(?:\s*[x×]\s*\d+)?$", re.IGNORECASE)
    SIZE_MM = re.compile(r"^\d+\s*mm$", re.IGNORECASE)
    VER_TOKEN = re.compile(r"^v?\d{1,2}[a-z]?$", re.IGNORECASE)
    NUM2 = re.compile(r"^\d{2}$")
    UV_WORD = re.compile(r"\buv\b", re.IGNORECASE)

    def _norm(text: str) -> str:
        t = unicodedata.normalize("NFKC", text or "")
        return re.sub(r"\s+", " ", t).strip()

    def _split_clean(s: str) -> List[str]:
        return [tok.strip(" ,-/") for tok in s.split() if tok.strip(" ,-/")]

    def _is_color(tok: str) -> bool:
        return tok.lower() in COLOR_WORDS

    def _is_version_phrase(s: str) -> bool:
        low = s.lower()
        if low in VERSION_PHRASES:
            return True
        if "special edition" in low or "anniversary" in low:
            return True
        if "ball-core" in low or "magnetic core" in low or "core magnets" in low:
            return True
        if UV_WORD.search(low) or "uv coated" in low:
            return True
        if low.endswith("edition"):
            return True
        return False

    def _token_starts_model(tok: str) -> bool:
        low = tok.lower()
        if VER_TOKEN.match(tok) or NUM2.match(tok):
            return True
        parts = re.split(r"[-/ ]", low)
        return any(
            p
            in {
                "wr",
                "wrm",
                "v",
                "v2",
                "v3",
                "v4",
                "v5",
                "v6",
                "v7",
                "v8",
                "v9",
                "v10",
                "v11",
            }
            for p in parts
        )

    name = _norm(raw_name)
    brand_tokens = _split_clean(raw_brand or "")

    # base (without parens) and tokens
    base = re.sub(r"\([^)]*\)", "", name)
    base_tokens = _split_clean(base)

    series_tokens: List[str] = []
    model_tokens: List[str] = []
    version_tags: List[str] = []

    start_model = False
    saw_any_modelish = False

    i = 0
    while i < len(base_tokens):
        tok = base_tokens[i]
        low = tok.lower()

        # sizes
        if SIZE_NxN.match(low):
            # keep NxN if it's the actual variant or we already flipped to model
            if start_model or not saw_any_modelish:
                model_tokens.append(tok)
                saw_any_modelish = True
            i += 1
            continue
        if SIZE_MM.match(low):
            model_tokens.append(tok)
            saw_any_modelish = True
            i += 1
            continue

        # UV token (route later)
        if UV_WORD.search(low) or low in {"uv-coated", "uvcoated"}:
            i += 1
            continue

        # decide boundary
        token_starts_model = _token_starts_model(tok) or (low in MODEL_FEATURE_TOKENS)
        if not start_model:
            if token_starts_model and series_tokens:
                start_model = True
                saw_any_modelish = True
            else:
                series_tokens.append(tok)
                i += 1
                continue

        # in model section
        if _is_version_phrase(tok) or _is_color(tok):
            version_tags.append(tok)
        else:
            model_tokens.append(tok)
        saw_any_modelish = True
        i += 1

    # Brand + leading number/alpha → attach to last series token with a space
    if brand_tokens and series_tokens:
        bt = [t.lower() for t in brand_tokens]
        st = [t.lower() for t in series_tokens[: len(brand_tokens)]]
        if bt == st and model_tokens:
            m0 = model_tokens[0]
            if (m0.isdigit() and 1 <= len(m0) <= 2) or re.match(
                r"^\d{1,2}[a-z]+$", m0, re.I
            ):
                series_tokens[-1] = f"{series_tokens[-1]} {m0}"
                model_tokens = model_tokens[1:]

    # Scan parentheticals and route
    for segment in re.findall(r"\(([^()]*)\)", name):
        for piece in re.split(r"[,/]", segment):
            cand = piece.strip(" -/")
            if not cand:
                continue
            low = cand.lower()
            if SIZE_NxN.match(low) or SIZE_MM.match(low):
                model_tokens.append(cand)
                continue
            if _is_version_phrase(cand) or _is_color(cand):
                version_tags.append(cand)
                continue
            if low in MODEL_FEATURE_TOKENS:
                model_tokens.append(cand)
            else:
                version_tags.append(cand)

    # UV routing: keep as version tag unless it's tightly "M UV" in model
    model_str = " ".join(model_tokens).strip()
    if UV_WORD.search(name) or any("uv coated" in t.lower() for t in version_tags):
        if not (
            UV_TIGHT_IN_MODEL and re.search(r"\bM\s+UV\b", model_str, re.IGNORECASE)
        ):
            # keep canonical "UV" once
            version_tags = [t for t in version_tags if "uv coated" not in t.lower()]
            if not any(UV_WORD.search(t) for t in version_tags):
                version_tags.append("UV")

    # format/dedupe version tags
    def _fmt_tag(t: str) -> str:
        t = t.strip()
        if t.upper() in {"UV", "FX", "MAX"}:
            return t.upper()
        if any(
            ch.isupper() for ch in t[1:]
        ):  # preserve existing style like "Ball-Core"
            return t
        return t.title()

    seen = set()
    deduped = []
    for t in version_tags:
        key = t.lower().strip()
        if key not in seen:
            seen.add(key)
            deduped.append(_fmt_tag(t))

    version_name = " + ".join(deduped)

    parsed_series = " ".join(series_tokens).strip() or (raw_brand or "")
    parsed_model = model_str or (raw_name or "")

    return parsed_series, parsed_model, version_name


def prepare_insert_payload(
    merged: Specs,
    submitted_by_id: Optional[str],
    vendor_links: List[VendorLinkCandidate],
) -> Tuple[
    CubeDBSchema, List[CubeFeaturesDBSchema], List[VendorLinkInsertPayload]
]:
    logger.info("Preparing data for insert into the database...")

    if submitted_by_id is None:
        logger.error("Missing user_id for job; aborting insert preparation.")
        sys.exit(1)

    insert_payload: CubeDBSchema = {
        "brand": "",
        "image_url": "",
        "model": "",
        "slug": "",
        "type": "",
        "discontinued": False,
        "release_date": None,
        "series": "",
        "sub_type": None,
        "weight": 0.0,
        "related_to": None,
        "version_type": "Base",
        "version_name": "",
        "surface_finish": None,
        "size": None,
        "submitted_by_id": submitted_by_id,
    }

    features_payload: List[CubeFeaturesDBSchema] = []

    raw_name = merged.get("name") or ""
    raw_brand = (merged.get("brand") or "").strip()

    parsed_series, parsed_model, parsed_version_name = parse_series_and_model(
        raw_name, raw_brand
    )

    insert_payload["series"] = parsed_series
    insert_payload["model"] = parsed_model
    insert_payload["version_name"] = parsed_version_name

    if not insert_payload["slug"]:
        cube_name = parsed_series + " " + parsed_model + " " + parsed_version_name
        slug_source = cube_name
        if slug_source:
            insert_payload["slug"] = slugify(slug_source)

    for key in list(insert_payload.keys()):
        if key in {"model", "series", "version_name", "submitted_by_id"}:
            continue
        merged_value = merged.get(key)

        if key == "size" and merged_value is not None:
            insert_payload[key] = format_dimensions(str(merged_value))

        elif key in {
            "magnetic",
            "maglev",
            "smart",
            "stickered",
            "wca_legal",
            "modded",
            "ball_core",
        }:
            if merged_value is True and insert_payload["slug"]:
                features_payload.append(
                    {"feature": key, "cube": insert_payload["slug"]}
                )

        elif merged_value is not None:
            insert_payload[key] = merged_value

    # Vendor Links

    vendor_links_payload: List[VendorLinkInsertPayload] = []
    slug = insert_payload.get("slug", "")
    if not slug:
        logger.warning("Unable to prepare vendor links payload without a cube slug.")
        return insert_payload, features_payload, vendor_links_payload

    for vendor_link in vendor_links:
        payload: VendorLinkInsertPayload = {
            "vendor_name": vendor_link["vendor_name"],
            "url": vendor_link["url"],
            "cube_slug": slug,
        }
        if vendor_link["price"] is not None:
            payload["price"] = float(vendor_link["price"])
        if vendor_link["available"] is not None:
            payload["available"] = bool(vendor_link["available"])
        vendor_links_payload.append(payload)

    return insert_payload, features_payload, vendor_links_payload


def insert_to_database(
    insert_payload: CubeDBSchema,
    features_payload: List[CubeFeaturesDBSchema],
    vendor_links: List[VendorLinkInsertPayload],
):
    logger.info("Inserting data into the database...")
    try:
        supabase.table("cube_models").insert([insert_payload]).execute()
        if features_payload:
            supabase.table("cubes_model_features").insert(features_payload).execute()
        else:
            logger.info("No features to insert.")
        if vendor_links:
            supabase.table("cube_vendor_links").insert(vendor_links).execute()
        else:
            logger.info("No vendor links to insert.")
    except Exception:
        if debug:
            logger.exception("Error inserting data into the database.")
        else:
            logger.error(
                "Error inserting data into the database! Rerun with --debug for more details"
            )
        raise

    logger.info("Data successfully inserted into the database.")


def set_job_as_running(job_id: int):
    logger.info("Setting job as running...")
    try:
        supabase.table("cube_scrap_runs").update(
            {"status": "running", "started_at": "now()"}
        ).eq("id", job_id).execute()
    except:
        logger.exception("Error updating job status.")
        raise

    logger.info("Job successfully set as running.")


def set_job_as_done(job_id: int):
    logger.info("Setting job as done...")
    try:
        supabase.table("cube_scrap_runs").update(
            {"status": "done", "finished_at": "now()"}
        ).eq("id", job_id).execute()
    except Exception:
        if debug:
            logger.exception("Error setting job as done.")
        else:
            logger.error(
                "Error setting job as done! Rerun with --debug for more details"
            )
        raise

    logger.info("Job successfully set as done.")


def set_job_as_failed(job_id: int, error: str):
    logger.info("Setting job as failed...")
    try:
        supabase.table("cube_scrap_runs").update(
            {"status": "failed", "error_message": error, "finished_at": "now()"}
        ).eq("id", job_id).execute()
    except Exception:
        if debug:
            logger.exception("Error setting job as failed.")
        else:
            logger.error(
                "Error setting job as failed! Rerun with --debug for more details"
            )
        raise

    logger.info("Job successfully set as failed.")


def main() -> None:
    jobs = fetch_jobs(limit)
    for job in jobs:
        job_id = job["id"]
        user_id_value = job.get("user_id")
        submitted_by_id = user_id_value if user_id_value else None

        logger.info(
            "Next job fetched! id=%s submitted_by_id=%s", job_id, submitted_by_id
        )

        try:
            set_job_as_running(job_id)
            job_links = fetch_job_links(job_id)
            store_cube_details = fetch_store_cube_details(job_links)
            verify_cube_details(store_cube_details)
            vendor_links = prepare_vendor_links(job_links)
            merged_details = merge_cube_details(store_cube_details)
            insert_payload, features_payload, vendor_links_payload = prepare_insert_payload(
                merged_details, submitted_by_id, vendor_links
            )
            insert_to_database(insert_payload, features_payload, vendor_links_payload)
            set_job_as_done(job_id)
        except BaseException as e:
            set_job_as_failed(job_id, str(e))


if __name__ == "__main__":
    main()
