"""
Create all MongoDB collections from Database_Schema.txt table list.
Run from project root:
    python scripts/create_all_collections.py
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.database import close_db, get_client, get_db_name

COLLECTION_NAMES = [
    "bookings",
    "booking_payments",
    "cities",
    "feedback",
    "floorplans",
    "properties",
    "properties_images",
    "prospects",
    "prospect_events",
    "spaces",
    "tours",
    "tour_steps",
    "units",
    "units_images",
]


async def main() -> None:
    client = get_client()
    db = client[get_db_name()]
    existing = set(await db.list_collection_names())

    created = []
    skipped = []
    for name in COLLECTION_NAMES:
        if name in existing:
            skipped.append(name)
            continue
        await db.create_collection(name)
        created.append(name)

    print(f"Created {len(created)} collections: {created}")
    print(f"Already existed {len(skipped)} collections: {skipped}")
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
