"""
Supabase database connection
Uses supabase-py for REST API calls
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL: str = os.environ["SUPABASE_URL"]
SUPABASE_KEY: str = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# Singleton client
supabase: Client = get_supabase()
