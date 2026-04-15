"""
Append 5 "Unit" feedback rows per floorplan (for inventory → View full details popup).
Safe to run multiple times (adds more rows; modal shows latest 5 by created_at).

  python scripts/seed_inventory_floorplan_feedback.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.bootstrap_supabase import _require_db_url  # noqa: E402

import psycopg

_UNIT_FB_TEMPLATES: list[dict] = [
    {
        "rating": 4,
        "notes": "Liked layout; comparing to one other community this week.",
        "likes": ["Open kitchen", "Balcony size"],
        "improvements": [],
    },
    {
        "rating": 3,
        "notes": "Concerned about natural light in the main living area.",
        "likes": ["Bedroom dimensions"],
        "improvements": ["Brightness in living room", "Closet depth"],
    },
    {
        "rating": 5,
        "notes": "Strong interest — requested pricing on shorter lease term.",
        "likes": ["Finishes", "Noise level"],
        "improvements": [],
    },
    {
        "rating": 2,
        "notes": "Bathroom felt tight vs expectations from photos.",
        "likes": ["Location"],
        "improvements": ["Bathroom layout", "Storage"],
    },
    {
        "rating": 4,
        "notes": "Would revisit if similar unit on higher floor becomes available.",
        "likes": ["View from bedroom"],
        "improvements": ["Elevator wait at peak"],
    },
]


def main() -> None:
    db_url = _require_db_url()
    with psycopg.connect(db_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("select id from floorplans")
            fp_rows = cur.fetchall()
            if not fp_rows:
                print("No floorplans found; nothing to seed.")
                return
            cur.execute("select id from prospects limit 200")
            pr_rows = cur.fetchall()
            if not pr_rows:
                print("No prospects found; cannot seed feedback (profile_id).")
                return
            prospect_ids = [r[0] for r in pr_rows]
            n = 0
            for fp_idx, (fpid,) in enumerate(fp_rows):
                for j in range(5):
                    tpl = _UNIT_FB_TEMPLATES[j % len(_UNIT_FB_TEMPLATES)]
                    created = datetime.now(UTC) - timedelta(
                        days=j * 4 + (fp_idx % 5),
                        hours=(fp_idx + j * 3) % 20,
                    )
                    pr = prospect_ids[(fp_idx * 7 + j * 3) % len(prospect_ids)]
                    cur.execute(
                        """
                        insert into feedback (profile_id, raw_feedback, floorplan_id, type, booking_id, created_at)
                        values (%s,%s::jsonb,%s,%s,%s,%s)
                        """,
                        (str(pr), json.dumps(tpl), str(fpid), "Unit", None, created),
                    )
                    n += 1
            print(f"Inserted {n} feedback rows across {len(fp_rows)} floorplans.")


if __name__ == "__main__":
    main()
