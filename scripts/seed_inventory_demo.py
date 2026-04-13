"""
Insert the legacy demo inventory (30 vacant units) into the Supabase project
configured in .env (SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY).

Run from repo root:
  python scripts/seed_inventory_demo.py
  python scripts/seed_inventory_demo.py --wipe-all

``--wipe-all`` removes ALL rows from inventory-related tables (bookings, tour_steps, spaces,
units, floorplans, tours, properties, cities, etc.) before inserting the demo. Use only on a
non-production or empty project so you get exactly these 30 units in /api/inventory/vacant-units.

Requires tables: cities, properties, tours, floorplans, units, spaces, tour_steps, bookings,
property_images. Uses the same shapes as scripts/bootstrap_supabase.py.

Without ``--wipe-all``: deletes only rows that use the demo UUIDs, then inserts (safe if the DB
already had other inventory — but the API may still show a mix in the first 30 rows).
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from inventory_demo_rows import parse_demo_rows
from lead_demo_seed import delete_leads_demo, fp_id_for_unit, seed_leads


NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def _fp_id(unit_id: str) -> str:
    return fp_id_for_unit(unit_id)


def _client():
    from supabase import create_client

    url = os.getenv("SUPABASE_URL", "").strip()
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.getenv("SUPABASE_KEY", "").strip()
        or os.getenv("SUPABASE_ANON_KEY", "").strip()
    )
    if not url or not key:
        raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env")
    return create_client(url, key)


def _fp_id(unit_id: str) -> str:
    return str(uuid.uuid5(NS, f"floorplan:{unit_id}"))


def _tour_id(property_id: str) -> str:
    return str(uuid.uuid5(NS, f"tour:{property_id}"))


def _city_id() -> str:
    return str(uuid.uuid5(NS, "inventory-demo-city"))


def _wipe_table_by_pk(client, table: str, pk: str = "id", max_rounds: int = 500) -> None:
    """Delete all rows in batches (PostgREST has no TRUNCATE)."""
    rounds = 0
    while rounds < max_rounds:
        rounds += 1
        res = client.table(table).select(pk).limit(150).execute()
        rows = res.data or []
        if not rows:
            return
        ids = []
        for r in rows:
            v = r.get(pk)
            if v is not None:
                ids.append(str(v))
        if not ids:
            return
        for i in range(0, len(ids), 80):
            client.table(table).delete().in_(pk, ids[i : i + 80]).execute()


def _wipe_all_inventory_related(client) -> None:
    """Foreign-key-safe order for typical Supabase schema (matches bootstrap deletes)."""
    for tbl in (
        "booking_payments",
        "feedback",
        "prospect_events",
        "bookings",
        "tour_steps",
        "unit_images",
        "property_images",
        "spaces",
        "units",
        "floorplans",
        "tours",
        "prospects",
        "properties",
        "cities",
    ):
        try:
            _wipe_table_by_pk(client, tbl, "id")
        except Exception as e:
            print(f"Note: could not fully wipe {tbl}: {e}")


def _delete_demo(client, rows: list[dict]) -> None:
    unit_ids = [r["unit_id"] for r in rows]
    fp_ids = [_fp_id(u) for u in unit_ids]
    prop_ids = list({r["property_id"] for r in rows})
    tour_ids = [_tour_id(p) for p in prop_ids]

    def _del(table: str, col: str, ids: list[str]) -> None:
        if not ids:
            return
        for i in range(0, len(ids), 80):
            batch = ids[i : i + 80]
            client.table(table).delete().in_(col, batch).execute()

    _del("bookings", "floorplan_id", fp_ids)
    _del("tour_steps", "unit_id", unit_ids)
    _del("spaces", "unit_id", unit_ids)
    _del("unit_images", "unit_id", unit_ids)
    _del("units", "id", unit_ids)
    _del("floorplans", "id", fp_ids)
    _del("property_images", "property_id", prop_ids)
    _del("tours", "id", tour_ids)
    _del("properties", "id", prop_ids)
    client.table("cities").delete().eq("id", _city_id()).execute()


def _seed(client, rows: list[dict]) -> None:
    cid = _city_id()
    today = date.today()
    now = datetime.now(UTC)

    client.table("cities").upsert(
        {
            "id": cid,
            "name": "Demo City",
            "state": "CA",
            "country": "USA",
            "state_full_name": "California",
            "timezone": "America/Los_Angeles",
            "show_in_onboarding": True,
            "show_in_app": True,
        }
    ).execute()

    prop_ids = list({r["property_id"] for r in rows})
    for i, pid in enumerate(sorted(prop_ids), start=1):
        tid = _tour_id(pid)
        client.table("properties").upsert(
            {
                "id": pid,
                "name": next(r["property_name"] for r in rows if r["property_id"] == pid),
                "description": "Demo property (inventory seed)",
                "address": {"line1": f"{100 + i} Main St", "city": "Demo City", "state": "CA", "zip": "90000"},
                "latitude": 34.05 + (i * 0.01),
                "longitude": -118.25 - (i * 0.01),
                "units": 200,
                "floors": 5,
                "city_id": cid,
                "amenities": ["gym", "pool"],
                "website": f"https://property-{pid[:8]}.example.com",
                "concession": "1 month free",
                "payment_model": "Subscription",
                "timezone": "America/Los_Angeles",
                "neighborhood_name": f"District {i}",
                "go_live_date": str(today - timedelta(days=30 + i)),
                "tours_start_time": 9.0,
                "tours_end_time": 18.0,
                "internal_only": False,
                "housing_type": "multifamily",
                "year_built": 2010 + (i % 15),
                "pricing_term_strategy": "global_min",
            }
        ).execute()

        client.table("property_images").upsert(
            {"property_id": pid, "image_index": 1, "image_path": f"/images/properties/{i}.jpg"}
        ).execute()

        client.table("tours").upsert(
            {
                "id": tid,
                "title": f"Guided tour — {pid[:8]}",
                "description": "Seeded guided tour",
                "property_id": pid,
                "estimated_minutes": 30,
                "audio_sync_status": "Synced",
                "visible": True,
                "locked_for_sync": False,
                "tour_concession": "None",
            }
        ).execute()

    for r in rows:
        uid = r["unit_id"]
        pid = r["property_id"]
        fp = _fp_id(uid)
        tid = _tour_id(pid)
        code = r["unit_code"]
        br = r["bedrooms"]
        vd = r["vacancy_days"]
        apps_n = r["apps"]
        avail = today - timedelta(days=vd)
        move_in = datetime.now(UTC) - timedelta(days=vd)

        client.table("floorplans").upsert(
            {
                "id": fp,
                "name": f"FP-{code}",
                "description": "Demo floorplan",
                "bedrooms": br,
                "bathrooms": "1",
                "square_footage": str(700 + hash(uid) % 200),
                "pets_allowed": True,
                "amenities": ["balcony"],
                "tour_id": tid,
                "property_id": pid,
                "booking_availability": "available",
                "address": {"line1": "100 Main St"},
            }
        ).execute()

        client.table("units").upsert(
            {
                "id": uid,
                "property_id": pid,
                "description": "Demo unit",
                "unit": code,
                "floor": str((hash(code) % 10) + 1),
                "monthly_rent": 1400 + hash(uid) % 500,
                "move_in_date": move_in.isoformat(),
                "active": True,
                "floorplan_id": fp,
                "view": "city",
                "lease_months": 12,
                "net_effective_rent": 1300,
                "application_url": f"https://apply.example.com/{code}",
                "rentable": True,
                "tourable": True,
            }
        ).execute()

        client.table("spaces").insert(
            {
                "unit_id": uid,
                "is_affordable": False,
                "has_pricing": True,
                "make_ready_date": str(today),
                "availability_status": "available",
                "available_date": str(avail),
                "marketing_unit_number": code,
                "min_rent": 1200.0,
                "max_rent": 1600.0,
                "min_deposit": 300.0,
                "max_deposit": 500.0,
                "occupancy_type": "market",
                "rentable": True,
                "tourable": True,
            }
        ).execute()

        for step in range(1, 6):
            client.table("tour_steps").insert(
                {
                    "tour_id": tid,
                    "title": f"Step {step}",
                    "floor": step,
                    "type": "unit",
                    "feedback": "ok",
                    "unit_id": uid,
                    "index": step,
                    "floorplan_id": fp,
                }
            ).execute()

        for b in range(apps_n):
            start = now - timedelta(hours=12 * (b + 1))
            end = start + timedelta(minutes=45)
            bid = str(uuid.uuid4())
            prof = str(uuid.uuid4())
            client.table("bookings").insert(
                {
                    "id": bid,
                    "floorplan_id": fp,
                    "start_time": start.isoformat(),
                    "end_time": end.isoformat(),
                    "profile_id": prof,
                    "string_profile_id": prof,
                    "phone": "+15550001111",
                    "name": f"Applicant {code}-{b}",
                    "pin": {},
                    "qr_code": {},
                    "stratis_meta": {"source": "seed"},
                    "completion_state": {"state": "completed"},
                    "utm_source": "seed",
                    "utm_medium": "demo",
                    "utm_campaign": "inventory",
                    "utm_content": code,
                    "utm_term": "lease",
                    "status": "booked",
                }
            ).execute()

        # Extra applications in the 8–30d and 31–90d windows so inventory conversion differs by ?days=.
        if apps_n > 0:
            for extra_days in (22, 58):
                st = now - timedelta(days=extra_days, hours=abs(hash(str(uid))) % 12)
                end = st + timedelta(minutes=45)
                bid = str(uuid.uuid4())
                prof = str(uuid.uuid4())
                client.table("bookings").insert(
                    {
                        "id": bid,
                        "floorplan_id": fp,
                        "start_time": st.isoformat(),
                        "end_time": end.isoformat(),
                        "profile_id": prof,
                        "string_profile_id": prof,
                        "phone": "+15550002222",
                        "name": f"Applicant {code}-hist-{extra_days}d",
                        "pin": {},
                        "qr_code": {},
                        "stratis_meta": {"source": "seed", "window": "historical"},
                        "completion_state": {"state": "completed"},
                        "utm_source": "seed",
                        "utm_medium": "demo",
                        "utm_campaign": "inventory",
                        "utm_content": code,
                        "utm_term": "lease",
                        "status": "booked",
                    }
                ).execute()


def main() -> None:
    ap = argparse.ArgumentParser(description="Seed legacy inventory demo into Supabase")
    ap.add_argument(
        "--wipe-all",
        action="store_true",
        help="Delete ALL inventory-related rows first (destructive; demo DB only)",
    )
    args = ap.parse_args()

    rows = parse_demo_rows()
    if len(rows) != 30:
        raise SystemExit(f"Expected 30 demo rows, got {len(rows)}")
    client = _client()
    if args.wipe_all:
        print("Wiping inventory-related tables (--wipe-all)…")
        _wipe_all_inventory_related(client)
    else:
        print("Removing previous demo leads (deterministic IDs)…")
        delete_leads_demo(client)
        print("Removing any previous demo rows with the same IDs…")
        _delete_demo(client, rows)
    print("Inserting cities, properties, tours, floorplans, units, spaces, tour_steps, bookings…")
    _seed(client, rows)
    print("Inserting prospects, prospect_events, and lead bookings for /api/leads/summary…")
    seed_leads(client, rows)
    print(
        "Done. Check GET /api/inventory/vacant-units?days=7 and GET /api/leads/summary?days=7 "
        "(use --wipe-all on a demo DB if you still see mixed inventory)."
    )


if __name__ == "__main__":
    main()
