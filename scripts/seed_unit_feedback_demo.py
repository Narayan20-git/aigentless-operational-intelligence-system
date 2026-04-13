from __future__ import annotations

import os
import random
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def _client():
    url = os.getenv("SUPABASE_URL", "").strip()
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.getenv("SUPABASE_KEY", "").strip()
        or os.getenv("SUPABASE_ANON_KEY", "").strip()
    )
    if not url or not key:
        raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env")
    return create_client(url, key)


LIKES = [
    "In-Unit Laundry",
    "Central A/C",
    "Kitchen Island",
    "Quartz Countertop",
    "Hardwood Flooring",
    "Natural Light",
    "Storage Space",
]
IMPROVEMENTS = [
    "Lighting",
    "Storage",
    "Bathroom updates",
    "Appliance refresh",
    "Noise insulation",
    "Closet space",
    "Kitchen ventilation",
]
RATINGS = ["loved", "liked", "okay"]
COMMENTS = [
    "Good layout but can feel dark in afternoon.",
    "Loved the plan, pricing felt a bit high.",
    "Kitchen is nice, storage could be better.",
    "Overall solid; bathroom updates would help.",
    "Great unit but needs brighter lighting.",
]


def _count_rows_for_window(rows: list[dict], now: datetime, start_days: int, end_days: int) -> int:
    c = 0
    for r in rows:
        t = r.get("created_at")
        if not t:
            continue
        try:
            dt = datetime.fromisoformat(str(t).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
        except ValueError:
            continue
        age = (now - dt).days
        if start_days <= age <= end_days:
            c += 1
    return c


def _make_feedback_payload(rng: random.Random) -> dict:
    like_n = 2 + (rng.randint(0, 2))
    imp_n = rng.randint(0, 2)
    likes = rng.sample(LIKES, k=min(like_n, len(LIKES)))
    improvements = rng.sample(IMPROVEMENTS, k=min(imp_n, len(IMPROVEMENTS)))
    rating = rng.choice(RATINGS)
    return {
        "likes": likes,
        "rating": rating,
        "dislikes": "",
        "improvements": improvements,
        "additionalCommentsLikes": "",
        "additionalCommentsImprovements": rng.choice(COMMENTS) if rng.random() < 0.45 else "",
    }


def main() -> None:
    client = _client()
    now = datetime.now(UTC)

    sp = (
        client.table("spaces")
        .select("unit_id,availability_status")
        .limit(800)
        .execute()
    )
    vacant_unit_ids = {
        str(r.get("unit_id"))
        for r in (sp.data or [])
        if str(r.get("availability_status") or "").strip().lower() in {"available", "vacant", "unoccupied", "open"}
        and r.get("unit_id")
    }
    if not vacant_unit_ids:
        raise SystemExit("No vacant units found in spaces.")

    units: list[dict] = []
    ids = list(vacant_unit_ids)
    for i in range(0, len(ids), 80):
        ur = (
            client.table("units")
            .select("id,unit,floorplan_id")
            .in_("id", ids[i : i + 80])
            .execute()
        )
        units.extend(ur.data or [])

    inserted = 0
    processed = 0
    for u in units:
        uid = str(u.get("id") or "")
        fp = str(u.get("floorplan_id") or "")
        if not uid or not fp:
            continue
        processed += 1
        rng = random.Random(uid)

        fr = (
            client.table("feedback")
            .select("created_at,floorplan_id,type")
            .eq("floorplan_id", fp)
            .eq("type", "Unit")
            .limit(1200)
            .execute()
        )
        rows = fr.data or []
        c_0_6 = _count_rows_for_window(rows, now, 0, 6)
        c_7_29 = _count_rows_for_window(rows, now, 7, 29)
        c_30_89 = _count_rows_for_window(rows, now, 30, 89)

        needs = [
            ("0_6", max(0, 5 - c_0_6), 0, 6),
            ("7_29", max(0, 5 - c_7_29), 7, 29),
            ("30_89", max(0, 5 - c_30_89), 30, 89),
        ]
        to_insert: list[dict] = []
        for bucket_name, deficit, lo, hi in needs:
            for idx in range(deficit):
                age_days = rng.randint(lo, hi)
                age_hours = rng.randint(0, 23)
                created_at = now - timedelta(days=age_days, hours=age_hours, minutes=rng.randint(0, 59))
                payload = _make_feedback_payload(rng)
                to_insert.append(
                    {
                        "profile_id": str(uuid.uuid4()),
                        "raw_feedback": payload,
                        "floorplan_id": fp,
                        "type": "Unit",
                        "booking_id": None,
                        "created_at": created_at.isoformat(),
                    }
                )
        if to_insert:
            for i in range(0, len(to_insert), 80):
                client.table("feedback").insert(to_insert[i : i + 80]).execute()
            inserted += len(to_insert)

    print(f"Processed units: {processed}")
    print(f"Inserted feedback rows: {inserted}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Failed: {e}")
        sys.exit(1)
