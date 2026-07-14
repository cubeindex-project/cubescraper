from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security
from pydantic import BaseModel, HttpUrl

from cubescraper.common.auth import jwks_auth, payload_injector
from cubescraper.common.exceptions import UnsupportedVendorError
from cubescraper.cube_info_scraper.cube_info_types import CubeInfoParserResult
from cubescraper.cube_info_scraper.exceptions import InvalidURLError, ParsingFailedError
from cubescraper.cube_info_scraper.main import process_job


class AutofillRequest(BaseModel):
    id: UUID
    url: HttpUrl


router = APIRouter(
    dependencies=[Security(jwks_auth)],
)


@router.post("/autofill", dependencies=[Depends(payload_injector)])
async def autofill(req: AutofillRequest) -> CubeInfoParserResult:
    job_id = req.id
    store_url = str(req.url).strip()

    if not store_url:
        raise HTTPException(status_code=400, detail="Invalid request")

    try:
        data = await process_job(job_id, store_url)
    except (InvalidURLError, UnsupportedVendorError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ParsingFailedError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="An internal error occurred")

    if not data:
        raise HTTPException(status_code=404, detail="No data found")

    return data
