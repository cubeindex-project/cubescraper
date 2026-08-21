from fastapi_jwks.dependencies.jwk_auth import JWKSAuth
from fastapi_jwks.injector import JWTTokenInjector
from fastapi_jwks.validators import JWKSValidator
from pydantic import BaseModel
from fastapi_jwks.injector import JWTTokenInjector
from fastapi_jwks.models.types import JWKSConfig, JWTDecodeConfig

from cubescraper.common.supabase import SUPABASE_URL


class SupabaseToken(BaseModel):
    sub: str
    email: str | None = None
    role: str | None = None


payload_injector = JWTTokenInjector[SupabaseToken]()

jwks_validator = JWKSValidator[SupabaseToken](
    decode_config=JWTDecodeConfig(audience=["authenticated"]),
    jwks_config=JWKSConfig(url=f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"),
)

jwks_auth = JWKSAuth(jwks_validator=jwks_validator)
