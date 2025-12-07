from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi_jwks.dependencies.jwk_auth import JWKSAuth
from fastapi_jwks.injector import JWTTokenInjector
from fastapi_jwks.models.types import JWKSConfig, JWTDecodeConfig
from fastapi_jwks.validators import JWKSValidator
from pydantic import BaseModel

from cubescraper.cube_info_scraper.main import process_job


class AutofillRequest(BaseModel):
    id: int
    url: str


class SupabaseToken(BaseModel):
    sub: str
    email: str | None = None
    role: str | None = None


app = FastAPI()

payload_injector = JWTTokenInjector[SupabaseToken]()
jwks_config = JWKSConfig(
    url="https://spsqaktodgqnqbkgilxp.supabase.co/auth/v1/.well-known/jwks.json"
)
decode_config = JWTDecodeConfig(audience=["authenticated"])
jwks_validator = JWKSValidator[SupabaseToken](
    decode_config=decode_config,
    jwks_config=jwks_config,
)
jwks_auth = JWKSAuth(jwks_validator=jwks_validator)

app = FastAPI(dependencies=[Security(jwks_auth)])


@app.post("/autofill")
async def autofill(
    req: AutofillRequest,
    token: SupabaseToken = Depends(payload_injector),
):
    user_id = token.sub

    job_id = req.id
    store_url = req.url.strip()

    if not store_url:
        raise HTTPException(status_code=400, detail="Invalid request")

    try:
        data = await process_job(job_id, store_url)
    except Exception:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

    if not data:
        raise HTTPException(status_code=404, detail="No data found")

    return {"id": job_id, "user_id": user_id, "autofilled": data}
