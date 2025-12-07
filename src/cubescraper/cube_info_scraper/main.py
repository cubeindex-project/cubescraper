import argparse
import logging
from uuid import UUID

from cubescraper.common.http import async_fetch_web_page
from cubescraper.common.logging import setup_logging
from cubescraper.cube_info_scraper.cube_info_types import ParserResult
from cubescraper.cube_info_scraper.parser import parse_cube_details

setup_logging()
logger = logging.getLogger(__name__)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

parser = argparse.ArgumentParser(
    "Fetch cube info",
    description="Fetch cube details from a cube store link.",
)


async def process_job(job_id: UUID, job_link: str) -> ParserResult:
    logger.info("Next job fetched! id=%s", job_id)
    try:
        html = await async_fetch_web_page(job_link)
        if not html:
            raise RuntimeError("Failed to fetch web page.")

        cube_details = parse_cube_details(html, job_link)
        if not cube_details:
            raise RuntimeError(
                f"No cube details were found for this link. ({job_link})"
            )

    except Exception:
        logger.exception("Job failed id=%s url=%s", job_id, job_link)
        raise

    logger.info("Job completed successfully! id=%s", job_id)
    logger.debug("Output: %s", cube_details)
    return cube_details
