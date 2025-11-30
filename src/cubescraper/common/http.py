import asyncio
import logging
from typing import Optional

import httpx

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"
    ),
    "Accept": "text/html",
}

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10.0
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0


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
            # Ignore malformed header; we will fall back to exponential backoff
            retry_after = None

    if retry_after is not None:
        return retry_after

    # Fallback to exponential backoff if Retry-After is missing/invalid
    return INITIAL_BACKOFF * (2 ** (attempt - 1))


def _backoff_delay(attempt: int) -> float:
    """Generic exponential backoff helper."""
    return INITIAL_BACKOFF * (2 ** (attempt - 1))


def fetch_web_page(url: str) -> Optional[str]:
    return asyncio.run(async_fetch_web_page(url))


async def async_fetch_web_page(url: str) -> Optional[str]:
    async with httpx.AsyncClient(
        headers=DEFAULT_HEADERS,
        follow_redirects=True,
        timeout=DEFAULT_TIMEOUT,
    ) as client:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = await client.get(url)

                delay = _retry_delay_for_response(resp, attempt)
                if delay is not None and attempt < MAX_RETRIES:
                    logger.warning(
                        "429 Too Many Requests for %s — retrying after %.1fs "
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

            except httpx.HTTPStatusError as exc:
                code = exc.response.status_code if exc.response is not None else None
                logger.error(
                    "HTTP error fetching %s : status %s (attempt %d/%d)",
                    url,
                    code,
                    attempt,
                    MAX_RETRIES,
                )
                break

            except httpx.HTTPError as exc:
                logger.error(
                    "Unexpected HTTPX error fetching %s: %s (attempt %d/%d)",
                    url,
                    exc,
                    attempt,
                    MAX_RETRIES,
                    exc_info=True,
                )
                if attempt < MAX_RETRIES:
                    delay = _backoff_delay(attempt)
                    await asyncio.sleep(delay)

        logger.error("Max retries reached for %s — giving up", url)
        return None
