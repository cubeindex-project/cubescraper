import os
import sys

from dotenv import load_dotenv
from supabase import AsyncClient, Client, acreate_client, create_client

load_dotenv(".env.local")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
if not (SUPABASE_URL and SUPABASE_SERVICE_KEY):
    sys.exit("❌  SUPABASE_URL or SUPABASE_SERVICE_KEY missing in .env.local")


def create_supabase_client() -> Client:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return supabase


async def create_async_supabase_client() -> AsyncClient:
    supabase: AsyncClient = await acreate_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return supabase
