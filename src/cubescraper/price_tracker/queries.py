import logging
from typing import cast

from cubescraper.common.common_types import JSON
from cubescraper.common.database_types import (
    PublicCubeVendorLinks,
    PublicCubeVendorLinksUpdate,
)
from cubescraper.common.supabase import (
    create_async_supabase_client,
)

logger = logging.getLogger(__name__)


async def fetch_vendor_links() -> list[PublicCubeVendorLinks]:
    supabase = await create_async_supabase_client()
    try:
        response = await supabase.table("cube_vendor_links").select("*").execute()
        return [PublicCubeVendorLinks(**cast(dict, row)) for row in response.data]
    except Exception as e:
        logger.exception("Failed to fetch vendor links from database: %r", e)
        raise


async def update_vendor_link(payload: PublicCubeVendorLinksUpdate, commit: bool):
    if not commit:
        logger.info("Dry-run: not updating database. Payload: %r", payload)
        return

    try:
        supabase = await create_async_supabase_client()
        response = await (
            supabase.table("cube_vendor_links")
            .update(cast(JSON, payload))
            .eq("id", payload.get("id"))
            .execute()
        )
    except Exception:
        logger.exception(
            "Exception during database update",
        )
        raise
    else:
        logger.info(
            "Successfully updated vendor link: %r",
            response.data,
        )


async def get_enabled_vendors() -> list[str]:
    try:
        supabase = await create_async_supabase_client()
        response = await (
            supabase.table("vendors")
            .select("base_url")
            .eq("supports_price_scraping", True)
            .execute()
        )
    except Exception as exc:
        logger.warning("Failed to fetch allowed types from Supabase: %s", exc)
        raise

    supported_vendors = [cast(dict, row)["base_url"] for row in response.data]
    logger.debug("Supported vendors: %s", supported_vendors)
    return supported_vendors


async def update_vendor_link_dead_status(link_id: int, is_dead: bool, commit: bool):
    if not commit:
        logger.info("Dry-run: not updating vendor link dead status to %s", is_dead)
        return

    payload = {"is_dead": is_dead}

    try:
        supabase = await create_async_supabase_client()
        response = (
            await supabase.table("cube_vendor_links")
            .update(cast(JSON, payload))
            .eq("id", link_id)
            .execute()
        )
    except Exception:
        logger.exception(
            "Exception during link's status update for id=%r: %r",
            link_id,
        )
        raise
    else:
        logger.info(
            "Successfully updated vendor link status id=%r: %r",
            link_id,
            response.data,
        )
