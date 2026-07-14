import asyncio
from typing import Optional

import httpx

from cubescraper.common.logging import logging

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}
DEFAULT_TIMEOUT = 10.0
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0


def _backoff_delay(attempt: int) -> float:
    """Generic exponential backoff helper."""
    return INITIAL_BACKOFF * (2 ** (attempt - 1))


def _retry_delay_for_response(resp: httpx.Response, attempt: int) -> Optional[float]:
    """
    Return delay in seconds if this response should be retried, otherwise None.
    Currently: retry on 429 Too Many Requests using Retry-After or exponential backoff.
    """
    if resp.status_code != 429:
        return None

    retry_after_header = resp.headers.get("Retry-After")
    retry_after: Optional[float] = None

    if retry_after_header is not None:
        try:
            retry_after = float(retry_after_header)
        except ValueError:
            retry_after = None

    if retry_after is not None:
        return retry_after

    # Fallback to exponential backoff if Retry-After is missing/invalid
    return _backoff_delay(attempt)


def fetch_web_page(url: str, follow_redirects: bool = False) -> Optional[str]:
    return asyncio.run(async_fetch_web_page(url, follow_redirects))


async def async_fetch_web_page(url: str, follow_redirects: bool = False) -> str:
    async with httpx.AsyncClient(
        headers=DEFAULT_HEADERS,
        follow_redirects=follow_redirects,
        timeout=DEFAULT_TIMEOUT,
    ) as client:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = await client.get(url)

                delay = _retry_delay_for_response(resp, attempt)
                if delay and attempt < MAX_RETRIES:
                    logger.warning(
                        "429 Too Many Requests for %s: retrying after %.1fs "
                        "(attempt %d/%d)",
                        url,
                        delay,
                        attempt,
                        MAX_RETRIES,
                    )
                    await asyncio.sleep(delay)
                    continue

                resp.raise_for_status()
                return resp.text

            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                logger.warning(
                    "Network error fetching %s: %s (attempt %d/%d)",
                    url,
                    exc,
                    attempt,
                    MAX_RETRIES,
                )
                if attempt < MAX_RETRIES:
                    delay = _backoff_delay(attempt)
                    await asyncio.sleep(delay)
                else:
                    raise

            except httpx.HTTPStatusError as exc:
                logger.error(
                    "HTTP error fetching %s : status %s (attempt %d/%d)",
                    url,
                    exc.response.status_code,
                    attempt,
                    MAX_RETRIES,
                )
                raise

            except httpx.HTTPError as exc:
                logger.error(
                    "Unexpected HTTPX error fetching %s: %s (attempt %d/%d)",
                    url,
                    exc,
                    attempt,
                    MAX_RETRIES,
                )
                if attempt < MAX_RETRIES:
                    delay = _backoff_delay(attempt)
                    await asyncio.sleep(delay)
                else:
                    raise

        logger.error("Max retries reached for %s: giving up", url)
        raise
