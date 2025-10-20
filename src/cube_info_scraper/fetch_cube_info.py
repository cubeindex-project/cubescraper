import argparse
import logging
import os
import re
import sys
import unicodedata

import requests
from datetime import date
from typing import Callable, Literal, Optional, TypedDict, Tuple, List, Dict, Any
from urllib.parse import urlparse
from rapidfuzz import fuzz
from slugify import slugify

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.common.supabaseClient import supabase

parser = argparse.ArgumentParser(
    "fetch_cube_info",
    description="Fetch job links and cube details from them to insert into the database.",
)
parser.add_argument("--debug", action="store_true", help="Enable DEBUG logs.")

args = parser.parse_args()
debug: bool = args.debug

logging.basicConfig(
    level=logging.DEBUG if debug else logging.INFO,
    format="%(levelname)s %(message)s",
)
logger = logging.getLogger("cube_info_scraper.fetch_cube_info")

if debug:
    logger.debug("Debug logging enabled.")

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


SUPPORTED_STORES = {"thecubicle.com", "speedcubeshop.com"}
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


def fetch_jobs() -> List[Dict[str, Any]]:
    logger.info("Fetching next job...")

    try:
        jobs = (
            supabase.table("cube_scrap_runs")
            .select("id, user_id")
            .order("created_at")
            .eq("status", "queued")
            .execute()
        )
    except Exception:
        logger.exception("Error fetching next job from Supabase.")
        raise

    if not jobs:
        logger.error("No jobs found!")
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
        raise

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
        raise

    logger.info("All links match the same cube.")


def merge_cube_details(store_cube_details: list[Specs]) -> Specs:
    logger.info("Merging store cube details...")

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
    }

    for row in store_cube_details:
        for key, value in row.items():
            old_value = merged.get(key)

            if key == "release_date":
                if not old_value or value < old_value:
                    merged[key] = str(value) if value else None
            elif key == "image_url" and old_value is None:
                merged[key] = str(value)
            elif key in (
                "magnetic",
                "maglev",
                "smart",
                "stickered",
                "wca_legal",
                "modded",
                "ball_core",
            ):
                merged[key] = False if value is None else bool(value)
            else:
                merged[key] = value

    logger.info("Successfully merged store cube details.")
    return merged


def parse_series_and_model(raw_name: str, raw_brand: str) -> tuple[str, str, str]:
    parsed_model_tokens: list[str] = []
    parsed_version_name = ""

    if raw_name:
        normalized_name = unicodedata.normalize("NFKC", raw_name)
        normalized_name = re.sub(r"\s+", " ", normalized_name).strip()

        size_pattern = re.compile(r"^\d+\s*x\s*\d+(?:\s*x\s*\d+)?$", re.IGNORECASE)
        version_token_pattern = re.compile(r"^v?\d{1,2}[a-z]?$", re.IGNORECASE)
        numeric_variant_pattern = re.compile(r"^\d{2}$")
        ignore_tokens = {
            "stickerless",
            "stickered",
            "stickers",
            "speed",
            "cube",
            "cubes",
            "smart",
            "puzzle",
            "with",
            "edition",
            "bundle",
            "set",
            "standard",
            "coated",
            "m",
        }
        model_start_keywords = {
            "maglev",
            "magnetic",
            "pioneer",
            "ball-core",
            "ballcore",
            "core",
            "core-magnets",
            "double-track",
            "double",
            "track",
            "max",
            "plus",
            "pro",
            "elite",
            "flagship",
            "enhanced",
            "super",
            "primary",
            "halo",
            "tornado",
            "wrm",
            "rs3m",
            "rs3",
            "shadow",
            "nebula",
            "spark",
            "lite",
            "light",
        }
        drop_from_model = {"magnetic"}

        base_without_parens = re.sub(r"\([^)]*\)", "", normalized_name)
        base_tokens = [
            token.strip(" ,-/")
            for token in base_without_parens.split()
            if token.strip(" ,-/")
        ]

        if re.search(r"\buv\b", normalized_name, re.IGNORECASE):
            parsed_version_name = "UV"

        series_tokens: list[str] = []
        start_model = False

        for token in base_tokens:
            cleaned = token.strip(" ,-/")
            if not cleaned:
                continue

            ascii_token = cleaned.lower().replace("A-", "x")
            if size_pattern.match(ascii_token):
                continue

            lower = cleaned.lower()
            if "uv" in lower:
                parsed_version_name = "UV"
                continue

            if lower in ignore_tokens:
                if not start_model and lower in model_start_keywords and series_tokens:
                    start_model = True
                continue

            token_starts_model = False
            if version_token_pattern.match(cleaned):
                token_starts_model = True
            elif numeric_variant_pattern.match(cleaned):
                token_starts_model = True
            elif any(part in model_start_keywords for part in lower.split("-")):
                token_starts_model = True

            if not start_model:
                if token_starts_model and series_tokens:
                    start_model = True
                else:
                    series_tokens.append(cleaned)
                    continue

            if lower in drop_from_model or lower in ignore_tokens:
                continue

            parsed_model_tokens.append(cleaned)

        brand_tokens = raw_brand.split() if raw_brand else []

        if (
            brand_tokens
            and series_tokens
            and [tok.lower() for tok in series_tokens[: len(brand_tokens)]]
            == [tok.lower() for tok in brand_tokens]
            and parsed_model_tokens
        ):
            first_model_token = parsed_model_tokens[0]
            if first_model_token.isdigit() and len(first_model_token) <= 2:
                series_tokens[-1] = f"{series_tokens[-1]}{first_model_token}"
                parsed_model_tokens = parsed_model_tokens[1:]

        parenthetical_tokens: list[str] = []
        for segment in re.findall(r"\(([^()]*)\)", normalized_name):
            for piece in re.split(r"[,/]", segment):
                candidate = piece.strip(" -/")
                if not candidate:
                    continue
                ascii_candidate = candidate.lower().replace("A-", "x")
                if size_pattern.match(ascii_candidate):
                    continue
                candidate_lower = candidate.lower()
                if "uv" in candidate_lower:
                    parsed_version_name = "UV"
                    continue
                if (
                    candidate_lower in ignore_tokens
                    or candidate_lower in drop_from_model
                ):
                    continue
                parenthetical_tokens.append(candidate)

        seen_model_tokens = {token.lower(): token for token in parsed_model_tokens}
        for token in parenthetical_tokens:
            lowered = token.lower()
            if lowered not in seen_model_tokens:
                parsed_model_tokens.append(token)
                seen_model_tokens[lowered] = token

        parsed_series = " ".join(series_tokens).strip()
        if not parsed_series:
            parsed_series = raw_brand or ""
    else:
        parsed_series = raw_brand or ""

    parsed_model = " ".join(parsed_model_tokens).strip()
    if not parsed_model and raw_name:
        parsed_model = raw_name

    return parsed_series, parsed_model, parsed_version_name


def prepare_insert_payload(
    merged: Specs, submitted_by_id: Optional[str]
) -> Tuple[CubeDBSchema, List[CubeFeaturesDBSchema]]:
    logger.info("Preparing data for insert into the database...")

    if submitted_by_id is None:
        logger.error("Missing user_id for job; aborting insert preparation.")
        raise

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

        if key == "size":
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

    logger.info("Prepared %d feature rows for insert", len(features_payload))

    return insert_payload, features_payload


def insert_to_database(
    insert_payload: CubeDBSchema, features_payload: List[CubeFeaturesDBSchema]
):
    logger.info("Inserting data into the database...")
    try:
        supabase.table("cube_models").insert([insert_payload]).execute()
        if features_payload:
            supabase.table("cubes_model_features").insert(features_payload).execute()
        else:
            logger.info("No features to insert.")
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
    jobs = fetch_jobs()
    for job in jobs:
        job_id = job["id"]
        user_id_value = job.get("user_id")
        submitted_by_id = user_id_value if user_id_value else None

        logger.info(
            "Next job fetched! id=%s submitted_by_id=%s", job_id, submitted_by_id
        )

        try:
            job_links = fetch_job_links(job_id)
            store_cube_details = fetch_store_cube_details(job_links)
            verify_cube_details(store_cube_details)
            merged_details = merge_cube_details(store_cube_details)
            insert_payload, features_payload = prepare_insert_payload(
                merged_details, submitted_by_id
            )
            insert_to_database(insert_payload, features_payload)
            set_job_as_done(job_id)
        except BaseException as e:
            set_job_as_failed(job_id, str(e))


if __name__ == "__main__":
    main()
