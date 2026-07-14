from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security
from pydantic import BaseModel, HttpUrl

from cubescraper.common.exceptions import UnsupportedVendorError
from cubescraper.common.auth import jwks_auth, payload_injector
from cubescraper.cube_info_scraper.exceptions import InvalidURLError, ParsingFailedError
from cubescraper.price_tracker.main import autofill_price
from cubescraper.price_tracker.price_types import ParseResult


class PriceAutofillRequest(BaseModel):
    id: UUID
    url: HttpUrl


router = APIRouter(
    dependencies=[Security(jwks_auth)],
)


@router.post(
    "/autofill",
    dependencies=[Depends(payload_injector)],
)
async def autofill(req: PriceAutofillRequest) -> ParseResult:
    job_id = req.id
    job_url = str(req.url).strip()

    if not job_url:
        raise HTTPException(status_code=400, detail="Invalid request")

    try:
        data = await autofill_price(job_id, job_url)
    except (InvalidURLError, UnsupportedVendorError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ParsingFailedError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="An internal error occurred")

    if not data:
        raise HTTPException(status_code=404, detail="No data found")

    return data
