import os, sys

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv(".env.local")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
if not (SUPABASE_URL and SUPABASE_KEY):
    sys.exit("❌  SUPABASE_URL or SUPABASE_KEY missing in .env.local")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)