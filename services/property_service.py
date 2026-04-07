import asyncio
from typing import Any

from config.database import get_client


def _fetch_properties() -> list[dict[str, Any]]:
    response = get_client().table("properties").select("*").execute()
    return response.data or []


async def list_properties() -> list[dict[str, Any]]:
    return await asyncio.to_thread(_fetch_properties)
