#!/usr/bin/env python3
"""
Bulk-import every *_products.json in ./stores_products into the cube_models
table on Supabase, after cleaning + normalisation, and keep a local JSON dump
for manual inspection.

Run again at any time — conflicting rows are upserted instead of failing.
"""

from __future__ import annotations
import json, os, re, sys
from pathlib import Path
from html import unescape
from typing import List
from collections import OrderedDict

from dotenv import load_dotenv
from supabase import create_client, Client

from slugify import slugify

# ──────────────────────────────────────────────────────────────────────────────
# 0) Environment & Supabase client
# ──────────────────────────────────────────────────────────────────────────────
load_dotenv(".env.local")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
if not (SUPABASE_URL and SUPABASE_KEY):
    sys.exit("❌  SUPABASE_URL or SUPABASE_KEY missing in .env.local")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ──────────────────────────────────────────────────────────────────────────────
# 1) File locations
# ──────────────────────────────────────────────────────────────────────────────
STORES_DIR = Path("./stores_products")
OUTPUT_FILE = Path("./normalized_outputs/all_products_normalized.json")
OUTPUT_FILE.parent.mkdir(exist_ok=True)

# ──────────────────────────────────────────────────────────────────────────────
# 2)  Constants & helpers (unchanged – collapsible for brevity)
# ──────────────────────────────────────────────────────────────────────────────

LIMITED_KEYWORDS = ["limited", "anniversary", "special edition"]
ILLEGAL_CUBE_TYPES: set[str] = {
    # Electronic / powered cubes (even if “3×3”)
    "Smart Cube",
    "Bluetooth Cube",
    "Motorized Cube",
    "Robot Cube",
    # Transparency & single-colour shape-mods
    "Transparent Cube",
    "Clear Cube",
    "Ice Cube",
    "Mirror Cube",
    "Ghost Cube",
    "Axis Cube",
    "Fisher Cube",
    "Barrel Cube",
    # Large or irregular cuboids & bandaged puzzles
    "Cuboid",
    "2×2×3",
    "3×3×2",
    "3×3×4",
    "3×3×5",
    "Bandaged Cube",
    "Mixup Cube",
    # Shape-mods & morphixes with non-uniform colours
    "Mastermorphix",
    "Pyramorphix",
    "Master Pyraminx",
    # Oversize NxN beyond official 7×7
    "8×8 Cube",
    "9×9 Cube",
    "10×10 Cube",
    "11×11 Cube",
    "12×12 Cube",
    "13×13 Cube",
    "15×15 Cube",
    "17×17 Cube",
    "18×18 Cube",
    # Non-event dodecahedra and deepcut variants
    "Kilominx",
    "Gigaminx",
    "Teraminx",
    "Petaminx",
    # Square-2 and other non-event bandaged variants
    "Square-2",
    "Cubedron",
    # Novelty / gimmick cubes
    "Ivy Cube",
    "Gear Cube",
    "Helicopter Cube",
    "Redi Cube",
    "Sudokube",
    "Floppy Cube",
    "Infinity Cube",
    "Siamese Cube",
}
ILLEGAL_TAGS: set[str] = {
    # Connectivity / “smart-cube” features
    "smart",
    "bluetooth",
    "wifi",
    "wi-fi",
    "wireless",
    "app",
    "app-enabled",
    "connected",
    "cloud",
    "iot",
    # Electronic sensors & chips
    "sensor",
    "sensors",
    "gyroscope",
    "gyro",
    "accelerometer",
    "imu",
    "magnetometer",
    "cpu",
    "chip",
    "pcb",
    # Displays, indicators & lights
    "display",
    "screen",
    "lcd",
    "oled",
    "led",
    "light",
    "lights",
    "rgb",
    "neon",
    "matrix",
    # Power / charging hardware
    "battery",
    "rechargeable",
    "usb",
    "type-c",
    "charging",
    "lithium",
    "li-ion",
    "charger",
    "power",
    # Motors & automatic movement
    "motor",
    "motorized",
    "auto",
    "auto-turn",
    "autosolve",
    "self-turning",
    "self-solving",
    "robotic",
    "robot",
    "servo",
    # Audio / video extras
    "camera",
    "microphone",
    "speaker",
    "voice",
    "sound",
    "buzzer",
    # Transparent or see-through shells
    "transparent",
    "clear",
    "see-through",
    "crystal",
    "acrylic",
    "glass",
    # Misc powered gimmicks
    "timer",
    "hud",
    "projector",
    "hologram",
}
SKIP_PRODUCT_TYPES = {
    "accessories",
    "accessories bundle",
    "apparel - clearance",
    "after sale",
    "beanie",
    "blanket",
    "book",
    "bundle",
    "burr puzzle",
    "christmas",
    "coaching service",
    "competitions",
    "cube cover",
    "display case",
    "display time",
    "diecast model",
    "diy",
    "diy kits",
    "educational toy",
    "flashcards",
    "fidget",
    "fidget cube",
    "hat",
    "hoodie",
    "hardware",
    "hobby tools",
    "jacket",
    "jigsaw puzzle",
    "lanyard",
    "learning",
    "lube",
    "live events",
    "lucky dip",
    "mat",
    "model kit",
    "mug",
    "nanoblock",
    "office",
    "other",
    "pill​ow",
    "plastic blade",
    "plushie",
    "remote control car",
    "refurbished",
    "syringe",
    "sticker sets",
    "storage bag",
    "storage box",
    "stand",
    "shirt",
    "t-shirt",
    "timer",
    "timer accessories",
    "timer skin",
    "tools & accessories",
    "training courses",
    "toy",
    "water bottle",
    "wooden building block",
    "wooden learning board toy",
    "wooden puzzle",
    "halloween",
    "digital",
    "download",
    "test",
    "OPTIONS_HIDDEN_PRODUCT",
    "globo",
    "Sliding",
    "Pillow",
    "snake",
    "pin",
    "badge",
    "mouse",
    "pad",
    "Locking",
    "Klotski",
    "Ball",
    "Kreativity",
    "LMS",
    "Hanayama",
    "Jibbitz",
    "Keychain",
    "Lubricant",
    "Lubricant" "set",
    "Game",
    "mod",
    "service",
    "sticker",
    "Tetra",
    "Lifestyle",
    "Freebie",
    "Decals",
    "Pouch",
    "Logo",
    "blindfold",
    "gift"
}
SURFACE_MAP = {
    "uv": "UV Coated",
    "uvcoated": "UV Coated",
    "frosted": "Frosted",
    "matte": "Matte",
    "gloss": "Glossy",
    "soft-touch": "Soft Touch",
}
MM_PATTERN = re.compile(r"(\d{2}(?:\.\d)?)\s*mm", re.I)
NXN_PATTERN = re.compile(r"\b(\d)[x×](\d)\b", re.I)
SIZE_PATTERN = re.compile(r"^\d+x\d+", re.I)
VERSION_PATTERN = re.compile(r"^(v\d+|pro|plus|m)$", re.I)

DEFAULT_SIZE_MM = {"2x2": 50, "3x3": 56, "4x4": 60, "5x5": 62, "6x6": 65, "7x7": 69}
NOISE_WORDS = {...}


def should_skip(prod: dict) -> bool:
    product_type = prod.get("product_type", "").lower()
    return any(skip.lower() in product_type for skip in SKIP_PRODUCT_TYPES)


# --------------  utility helpers  (same bodies you already have) -------------
def detect_size_mm(prod: dict) -> float:
    """
    Look for a measurement in mm anywhere
    (title, description, tags, variant titles).
    Fallback to DEFAULT_SIZE_MM based on NxN,
    else default to 56 mm.
    """
    # 1) Direct “XX mm”
    text = " ".join(
        [
            prod.get("title", ""),
            unescape(prod.get("body_html") or ""),
            *prod.get("tags", []),
            *[v.get("title", "") for v in prod.get("variants", [])],
        ]
    ).lower()

    m = MM_PATTERN.search(text)
    if m:
        return float(m.group(1))

    # 2) NxN fallback
    m = NXN_PATTERN.search(prod.get("title", ""))
    if m:
        key = f"{m.group(1)}x{m.group(2)}"
        return DEFAULT_SIZE_MM.get(key, 56.0)

    # 3) Default to 56 mm
    return 56.0


def extract_series_name(title: str) -> str:
    """
    From “Brand XYZ 3x3 Pro - Limited Edition” extract “Brand XYZ”.
    """
    # Remove anything in parentheses
    clean = re.sub(r"\(.*?\)", "", title)

    # Drop anything after a dash
    clean = clean.split(" -", 1)[0]

    words = []
    for w in clean.split():
        lw = w.lower()
        if SIZE_PATTERN.match(lw) or VERSION_PATTERN.match(lw) or lw in NOISE_WORDS:
            break
        words.append(w)
    return " ".join(words).strip()


def detect_surface_finish(tags: list[str]) -> str | None:
    """Return a mapped surface finish if any keyword appears in tags."""
    for tag in tags:
        key = tag.lower().replace("_", "-").replace(" ", "")
        for kw, name in SURFACE_MAP.items():
            if kw in key:
                return name
    return None


def is_stickered(prod: dict) -> bool:
    """
    Heuristic based on variant titles & tags.
    - If “stickerless” appears → False
    - If “stickered” appears → True
    - If “black” or “primary” appears → assume stickers
    - Else default to False
    """
    text = " ".join(
        prod.get("tags", []) + [v.get("title", "") for v in prod.get("variants", [])]
    ).lower()

    if "stickerless" in text:
        return False
    if "stickered" in text or any(k in text for k in ("black", "primary")):
        return True
    return False


def deduplicate_rows(rows: list[dict]) -> list[dict]:
    """
    Keep only the first row for each (slug, version_type, version_name) key.
    Returns a list with stable order.
    """
    unique: OrderedDict[tuple[str, str, str], dict] = OrderedDict()
    for r in rows:
        key = r["slug"]
        # decide which row wins; here: first wins.  Swap if you prefer 'last wins'.
        if key not in unique:
            unique[key] = r
    return list(unique.values())


def normalize_product(prod: dict) -> list[dict]:
    """
    Turn one raw product into one or more “rows”:
    - If no variants → one Base row
    - If variants → first is Base, others are Trim
    """
    tags = [t.lower() for t in prod.get("tags", [])]
    base = {
        "series": extract_series_name(prod.get("title", "")),
        "model": prod.get("title", "")
        .replace(extract_series_name(prod.get("title", "")), "")
        .strip(),
        "slug": slugify(
            text=extract_series_name(prod.get("title", ""))
            + prod.get("title", "").replace(
                extract_series_name(prod.get("title", "")), ""
            )
        ),
        "brand": prod.get("vendor", ""),
        "type": prod.get("product_type", ""),
        "magnetic": "magnetic" in tags,
        "maglev": any("maglev" in t for t in tags),
        "smart": "bluetooth" in tags,
        "wca_legal": not any(t.lower() in ILLEGAL_TAGS for t in tags)
        and prod.get("product_type", "") not in ILLEGAL_CUBE_TYPES,
        "image_url": (prod.get("images") or [{}])[0].get("src", "").split("?", 1)[0],
        "discontinued": not any(
            v.get("available", True) for v in prod.get("variants", [])
        ),
        "surface_finish": detect_surface_finish(tags),
        "stickered": is_stickered(prod),
        "release_date": prod.get("published_at", "")[:10],
        "size": detect_size_mm(prod),
        "weight": 0,
        "rating": 0,
        "notes": "",
        "status": "Pending",
        "submitted_by": "CubeIndex",
        "version_type": "Base",
        "version_name": "",
    }

    variants = prod.get("variants") or []
    rows = [base]

    if variants:
        # First variant = Base; others = Trim
        for v in variants:
            row = base.copy()
            row["weight"] = v.get("grams", 0)
            row["related_to"] = row["slug"]
            row["slug"] = slugify(text=row["slug"] + " " + v.get("title", ""))
            row["version_type"] = "Trim"
            row["version_name"] = v.get("title", "")
            if v.get("featured_image", None) != None:
                row["image_url"] = v["featured_image"].get("src")
            rows.append(row)

    return rows


# ──────────────────────────────────────────────────────────────────────────────
# 3)  Supabase write helper
# ──────────────────────────────────────────────────────────────────────────────
def write_rows_to_supabase(rows: list[dict], chunk: int = 500) -> None:
    """
    Insert (or upsert) rows in ≤500-record chunks to avoid the 1 000-row REST cap.
    Duplicate primary-key rows are merged (UPSERT) so the script is re-runnable.
    """
    for start in range(0, len(rows), chunk):
        batch = rows[start : start + chunk]
        # On‐conflict columns must match the PK/unique constraint in your table.
        supabase.table("cube_models").upsert(batch, on_conflict="slug").execute()


# ──────────────────────────────────────────────────────────────────────────────
# 4)  Main routine
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    all_rows: list[dict] = []
    files = sorted(STORES_DIR.glob("*_products.json"))

    for fp in files:
        with fp.open(encoding="utf-8") as f:
            products = json.load(f)

        for prod in products:
            if should_skip(prod):
                continue
            all_rows.extend(normalize_product(prod))

        print(f"✓  {fp.name:<32} → {len(products):>3} items scanned")

    if not all_rows:
        print("⚠️  Nothing suitable found – exiting.")
        return

    print(f"🔍  Deduplicating {len(all_rows)} candidate rows …")
    all_rows = deduplicate_rows(all_rows)
    print(f"✅  {len(all_rows)} unique rows remain after deduplication")

    # 1) Write to Supabase
    print(f"⏳  Uploading {len(all_rows)} rows to Supabase …")
    write_rows_to_supabase(all_rows)
    print("✅  Supabase upload complete.")

    # 2) Save local review file
    OUTPUT_FILE.write_text(
        json.dumps(all_rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"💾  Normalised dump saved → {OUTPUT_FILE}")

    print(
        f"\n🎉  Finished: {len(all_rows)} rows imported from {len(files)} source files"
    )


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
