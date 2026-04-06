"""
Seed sample leads. Run from project root:
    python scripts/seed_leads.py
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


async def main() -> None:
    from config.database import close_db, init_db
    from models.lead_model import Lead

    await init_db()
    await Lead.delete_all()

    now = datetime.now(timezone.utc)
    samples = [
        Lead(
            name="Sarah Martinez",
            status="Hot",
            priority="critical",
            property="Oak Residences",
            unit="Unit 2B",
            tour_time=now + timedelta(days=2, hours=14),
            last_contact_hours=2,
            tags=["Concerned about bathroom size", "Price sensitivity"],
        ),
        Lead(
            name="Jordan Lee",
            status="Hot",
            priority="moderate",
            property="Harbor Point Towers",
            unit="Unit 1204",
            tour_time=now + timedelta(days=1, hours=10),
            last_contact_hours=5,
            tags=["Wants east-facing windows", "Flexible on move-in"],
        ),
        Lead(
            name="Priya Shah",
            status="Warm",
            priority="moderate",
            property="Maple Grove Commons",
            unit="Unit 5A",
            tour_time=now + timedelta(days=4, hours=15, minutes=30),
            last_contact_hours=18,
            tags=["Comparing two buildings", "Needs parking"],
        ),
        Lead(
            name="Marcus Chen",
            status="Warm",
            priority="low",
            property="Oak Residences",
            unit="Unit 8C",
            tour_time=now + timedelta(days=6, hours=11),
            last_contact_hours=40,
            tags=["First-time buyer", "Mortgage pre-approved"],
        ),
        Lead(
            name="Elena Rossi",
            status="Cold",
            priority="low",
            property="Riverside Lofts",
            unit="Unit 3D",
            tour_time=now + timedelta(days=10, hours=16),
            last_contact_hours=96,
            tags=["Follow up next quarter", "Traveling abroad"],
        ),
    ]
    for lead in samples:
        await lead.insert()

    await close_db()
    print(f"Successfully seeded {len(samples)} leads into collection 'leads'.")


if __name__ == "__main__":
    asyncio.run(main())
