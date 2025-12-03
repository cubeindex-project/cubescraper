import logging
from typing import List, cast

from cubescraper.common.common_types import JSON
from cubescraper.common.supabase import create_async_supabase_client
from cubescraper.price_tracker.price_types import CubeVendorLink, CubeVendorLinkPayload

logger = logging.getLogger(__name__)


async def fetch_vendor_links() -> List[CubeVendorLink]:
    supabase = await create_async_supabase_client()
    try:
        response = await supabase.table("cube_vendor_links").select("*").execute()
        data = cast(List[CubeVendorLink], response.data or [])
        return data
    except Exception as e:
        logger.exception("Failed to fetch vendor links from database: %r", e)
        return []


async def update_vendor_link(payload: CubeVendorLinkPayload, commit: bool):
    supabase = await create_async_supabase_client()
    if not commit:
        logger.info("Dry-run — not updating database. Payload: %r", payload)
        return

    try:
        response = await (
            supabase.table("cube_vendor_links")
            .update(cast(JSON, payload))
            .eq("id", payload["id"])
            .execute()
        )
    except Exception as e:
        logger.exception(
            "Exception during database update for id=%r: %r",
            payload.get("id"),
            e,
        )
    else:
        logger.info(
            "Successfully updated vendor link id=%r: %r",
            payload.get("id"),
            response.data,
        )
