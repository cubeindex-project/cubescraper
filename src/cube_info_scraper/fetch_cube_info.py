import sys, os, re, requests
from typing import TypedDict, Optional, Literal
from urllib.parse import urlparse
from rapidfuzz import fuzz

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.common.supabaseClient import supabase


def format_dimensions(text: str) -> str:
    """Normalize a cube dimension string into a consistent format."""
    if not text:
        return ""

    # Replace lowercase/uppercase x or * with a plain 'x'
    normalized = text.strip().lower().replace("*", "x").replace("a-", "x")

    # Remove 'mm' or similar unit suffixes
    normalized = re.sub(r"\s*mm\b", "", normalized, flags=re.IGNORECASE)

    # Add a single space around the x sign
    normalized = re.sub(r"\s*x\s*", " x ", normalized)

    # Collapse multiple spaces
    return re.sub(r"\s+", " ", normalized).strip()


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


SUPPORTED_STORES = ["thecubicle.com", "speedcubeshop.com"]


if __name__ == "__main__":
    print("Fetching next job...")

    try:
        jobId = (
            supabase.table("v_scrape_runs_status")
            .select("id")
            .order("created_at")
            .neq("status", "done")
            .limit(1)
            .maybe_single()
            .execute()
        )
    except:
        print("Error fetching next job! Rerun with --debug for more details")
        sys.exit()

    if not jobId:
        print("No next job found!")
        sys.exit()
    else:
        jobId = jobId.data["id"]
        print(f"Next job fetched! ID: {jobId}")
        rawJobLinks = (
            supabase.table("cube_scrap_runs_url")
            .select("normalized_url")
            .order("created_at")
            .eq("run_id", jobId)
            .execute()
        )

    print("Fetching job links...")
    jobLinks = []
    for row in rawJobLinks.data:
        link = row.get("normalized_url")
        jobLinks.append(link)

    if len(jobLinks) == 0:
        print("No job links found!")
        sys.exit()

    print(f"{len(jobLinks)} links fetched!")
    print("Processing job links...")

    store_cube_details: list[Specs] = []

    for i, link in enumerate(jobLinks, start=1):
        parsed_link = urlparse(link)
        if parsed_link.hostname not in SUPPORTED_STORES:
            print(f"Unsupported store: {parsed_link.hostname}")
            continue

        headers = {
            "User-Agent": "CubeIndexBot/1.0 (+support@cubeindex.app)",
            "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
        }
        resp = requests.get(link, headers, timeout=12.0)

        if parsed_link.hostname == "thecubicle.com":
            from src.cube_info_scraper.helpers.thecubicle import thecubicle_cube_details

            store_cube_details.append(thecubicle_cube_details(resp.text))
        elif parsed_link.hostname == "speedcubeshop.com":
            from src.cube_info_scraper.helpers.scs import scs_cube_details

            store_cube_details.append(scs_cube_details(resp.text))
        else:
            print(f"No parser implemented for {parsed_link.hostname}")
            continue

        print(f"Link {i}/{len(jobLinks)} processed!")

    print("All links processed!")
    print("Verifying data consistency across links...")

    SIMILARITY_THRESHOLD = 50  # percent
    verif_score = 0
    pairs_checked = 0

    for prev, curr in zip(store_cube_details, store_cube_details[1:]):
        name_a, name_b = prev.get("name", ""), curr.get("name", "")
        brand_a, brand_b = prev.get("brand", ""), curr.get("brand", "")
        type_a, type_b = prev.get("type", ""), curr.get("type", "")

        if not name_a or not name_b:
            print("Missing name in one of the entries, skipping...")
            continue

        if not brand_a or not brand_b:
            print("Missing name in one of the entries, skipping...")
            continue

        if not type_a or not type_b:
            print("Missing name in one of the entries, skipping...")
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

    if pairs_checked == 0:
        print("No valid name pairs to compare.")
        sys.exit(1)

    if verif_score != pairs_checked:
        print(
            f"Only {verif_score}/{pairs_checked} pairs matched (threshold {SIMILARITY_THRESHOLD}%)."
        )
        sys.exit(1)

    print("All links match the same cube!")
