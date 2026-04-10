"""
Populate prospects + prospect_events + bookings for GET /api/leads/summary
using existing properties and units (no inventory re-seed).

Run from repo root:
  python scripts/seed_leads_only.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
for p in (ROOT, SCRIPTS_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from lead_demo_seed import build_inventory_rows_from_db, delete_leads_demo, seed_leads, supabase_client


def main() -> None:
    client = supabase_client()
    rows = build_inventory_rows_from_db(client)
    if len(rows) < 3:
        raise SystemExit(
            "Need at least a few properties with units in the database. "
            "Run: python scripts/seed_inventory_demo.py (or restore your schema/data)."
        )
    print(f"Using {len(rows)} property/unit pairs from the database.")
    print("Removing previous demo leads (deterministic IDs)…")
    delete_leads_demo(client)
    print("Inserting 40 demo prospects, events, and bookings…")
    n = seed_leads(client, rows)
    print(f"Done. Inserted {n} prospects. GET /api/leads/summary?days=7 should return data.")


if __name__ == "__main__":
    main()
