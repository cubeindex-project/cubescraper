import os

from dotenv import load_dotenv
from supabase import AsyncClient, Client, acreate_client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")


def _get_supabase_credentials() -> tuple[str, str]:
    url = SUPABASE_URL
    service_key = os.getenv("SUPABASE_SECRET_KEY", "")
    if not (url and service_key):
        raise RuntimeError("SUPABASE_URL or SUPABASE_SECRET_KEY missing in environment")
    return url, service_key


def create_supabase_client() -> Client:
    url, service_key = _get_supabase_credentials()
    supabase: Client = create_client(url, service_key)
    return supabase


async def create_async_supabase_client() -> AsyncClient:
    url, service_key = _get_supabase_credentials()
    supabase: AsyncClient = await acreate_client(url, service_key)
    return supabase
