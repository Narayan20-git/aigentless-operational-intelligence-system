import asyncio
import logging
import os
from typing import Any

import httpx
from dotenv import load_dotenv
from postgrest.constants import DEFAULT_POSTGREST_CLIENT_TIMEOUT
from supabase import Client, ClientOptions, create_client

load_dotenv()

logger = logging.getLogger(__name__)

_client: Client | None = None
_http_session: httpx.Client | None = None
_db_ready = False


def get_supabase_url() -> str:
    return os.getenv("SUPABASE_URL", "").strip()


def get_supabase_key() -> str:
    return (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.getenv("SUPABASE_KEY", "").strip()
        or os.getenv("SUPABASE_ANON_KEY", "").strip()
    )


def get_client() -> Client:
    global _client, _http_session
    if _client is None:
        url = get_supabase_url()
        key = get_supabase_key()
        if not url or not key:
            raise RuntimeError(
                "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY/SUPABASE_KEY/SUPABASE_ANON_KEY in .env"
            )
        # PostgREST defaults to http2=True; HTTP/2 to Supabase often raises
        # httpx.RemoteProtocolError: Server disconnected on Windows / some networks.
        session = httpx.Client(
            http2=False,
            follow_redirects=True,
            timeout=DEFAULT_POSTGREST_CLIENT_TIMEOUT,
        )
        try:
            _client = create_client(
                url,
                key,
                ClientOptions(
                    httpx_client=session,
                    postgrest_client_timeout=DEFAULT_POSTGREST_CLIENT_TIMEOUT,
                ),
            )
        except Exception:
            session.close()
            raise
        _http_session = session
    return _client


def db_is_ready() -> bool:
    return _db_ready


def _ping_supabase() -> Any:
    client = get_client()
    return client.table("properties").select("id").limit(1).execute()


async def init_db() -> None:
    global _db_ready
    await asyncio.to_thread(_ping_supabase)
    _db_ready = True


async def startup_database() -> bool:
    global _db_ready
    _db_ready = False
    try:
        await init_db()
        return True
    except Exception:
        logger.exception("Supabase init failed. Check SUPABASE_URL and API key.")
        await close_db()
        return False


async def close_db() -> None:
    global _client, _http_session, _db_ready
    _db_ready = False
    if _http_session is not None:
        _http_session.close()
        _http_session = None
    _client = None
