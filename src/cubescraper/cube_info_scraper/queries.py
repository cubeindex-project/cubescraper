import logging
from functools import lru_cache
from typing import List, cast

from cubescraper.common.supabase import create_supabase_client

logger = logging.getLogger(__name__)


def _get_supabase_client():
    try:
        return create_supabase_client()
    except Exception as exc:
        logger.error("Failed to create Supabase client: %s", exc)
        return None


@lru_cache(maxsize=1)
def get_allowed_types() -> List[str]:
    supabase = _get_supabase_client()
    if supabase is None:
        return []

    try:
        response = supabase.table("cube_types").select("name").execute()
    except Exception as exc:
        logger.error("Failed to fetch allowed types from Supabase: %s", exc)
        return []

    return [cast(dict[str, str], row)["name"] for row in (response.data or [])]


@lru_cache(maxsize=1)
def get_allowed_brands() -> list[str]:
    supabase = _get_supabase_client()
    if supabase is None:
        return []

    try:
        response = supabase.table("brands").select("name").execute()
    except Exception as exc:
        logger.error("Failed to fetch brands from Supabase: %s", exc)
        return []

    return [cast(dict[str, str], row)["name"] for row in (response.data or [])]
