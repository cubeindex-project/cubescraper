import argparse
import logging
from uuid import UUID

from cubescraper.common.http import async_fetch_web_page
from cubescraper.common.utils import get_short_uuid
from cubescraper.cube_info_scraper.cube_info_types import CubeInfoParserResult
from cubescraper.cube_info_scraper.parser import parse_cube_details
from cubescraper.common.logging import log_context

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(
    "Fetch cube info",
    description="Fetch cube details from a cube store link.",
)


async def process_job(job_id: UUID, job_link: str) -> CubeInfoParserResult:
    short_job_id = get_short_uuid(job_id)
    token = log_context.set(f"job_id={short_job_id}")
    try:
        logger.info("Next job fetched! url=%s", job_link)
        try:
            html = await async_fetch_web_page(job_link, follow_redirects=True)
            if not html:
                logger.error("Failed to fetch web page. url=%s", job_link)
                raise RuntimeError("Failed to fetch web page.")

            cube_details = parse_cube_details(html, job_link)

        except Exception:
            logger.exception("Job failed url=%s", job_link)
            raise

        logger.info(
            "Job completed successfully!",
        )
        logger.debug("Job output: %s", cube_details)
        return cube_details
    finally:
        log_context.reset(token)
