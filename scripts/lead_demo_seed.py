"""Shared helpers to seed prospects / prospect_events / bookings for GET /api/leads/summary."""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
LEAD_NS = uuid.UUID("8d2b1f4e-3c0a-4b8e-9f1d-2a7e6c5b4a30")


def fp_id_for_unit(unit_id: str) -> str:
    return str(uuid.uuid5(NS, f"floorplan:{unit_id}"))


def demo_prospect_ids() -> list[str]:
    return [str(uuid.uuid5(LEAD_NS, f"demo-prospect-{i}")) for i in range(1, 41)]


PROSPECT_NAME_POOL = [
    ("Sarah", "Martinez"),
    ("Michael", "Chen"),
    ("Jessica", "Wilson"),
    ("Amanda", "Rodriguez"),
    ("David", "Park"),
    ("Priya", "Sharma"),
    ("Kevin", "Nguyen"),
    ("Emily", "Johnson"),
    ("Noah", "Davis"),
    ("Olivia", "Taylor"),
    ("Ethan", "Brown"),
    ("Sophia", "Anderson"),
    ("Daniel", "Lee"),
    ("Maya", "Patel"),
    ("Ryan", "Garcia"),
]


def supabase_client() -> Any:
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


def delete_leads_demo(client: Any) -> None:
    ids = demo_prospect_ids()

    def _del_in(table: str, col: str, batch_ids: list[str]) -> None:
        if not batch_ids:
            return
        for i in range(0, len(batch_ids), 80):
            client.table(table).delete().in_(col, batch_ids[i : i + 80]).execute()

    try:
        _del_in("prospect_events", "prospect_id", ids)
    except Exception:
        pass
    try:
        _del_in("bookings", "profile_id", ids)
    except Exception:
        pass
    try:
        _del_in("prospects", "id", ids)
    except Exception:
        pass


def first_unit_floorplan_by_property(rows: list[dict]) -> dict[str, tuple[str, str | None]]:
    """property_id -> (unit_id, floorplan_id or None)."""
    m: dict[str, tuple[str, str | None]] = {}
    for r in rows:
        pid = r["property_id"]
        if pid not in m:
            uid = r["unit_id"]
            fp = r.get("floorplan_id")
            m[pid] = (uid, str(fp) if fp else None)
    return m


def build_inventory_rows_from_db(client: Any, limit_props: int = 40) -> list[dict]:
    """Use existing properties + one unit each (for Lead seed when inventory demo was not used)."""
    pr = client.table("properties").select("id").order("name").limit(limit_props).execute()
    out: list[dict] = []
    for p in pr.data or []:
        pid = str(p["id"])
        ur = (
            client.table("units")
            .select("id,floorplan_id")
            .eq("property_id", pid)
            .order("unit")
            .limit(1)
            .execute()
        )
        if not ur.data:
            continue
        u = ur.data[0]
        uid = str(u["id"])
        fp = u.get("floorplan_id")
        out.append(
            {
                "unit_id": uid,
                "property_id": pid,
                "floorplan_id": str(fp) if fp else None,
            }
        )
    return out


def seed_leads(client: Any, inventory_rows: list[dict]) -> int:
    """Insert 40 demo prospects. inventory_rows: unit_id, property_id, optional floorplan_id."""
    m = first_unit_floorplan_by_property(inventory_rows)
    prop_ids = sorted(m.keys())
    if not prop_ids:
        return 0

    now = datetime.now(UTC)
    ids = demo_prospect_ids()

    for i, prid in enumerate(ids, start=1):
        fn, ln = PROSPECT_NAME_POOL[(i - 1) % len(PROSPECT_NAME_POOL)]
        prop = prop_ids[(i - 1) % len(prop_ids)]
        uid, fp_raw = m[prop]
        fp = fp_raw or fp_id_for_unit(uid)

        client.table("prospects").upsert(
            {
                "id": prid,
                "email": f"{fn.lower()}.{ln.lower()}{i}@example.com",
                "phone_number": f"+1555{i:07d}",
                "first_name": fn,
                "last_name": ln,
                "applied": i % 3 == 0,
                "leased": i % 8 == 0,
                "ignore": False,
                "ignore_dev": False,
            }
        ).execute()

        n_events = 3 if i % 4 == 0 else 2 if i % 3 == 0 else 1
        for j in range(n_events):
            ev_time = now - timedelta(hours=min(167, (i * 3 + j * 5) % 168))
            ev_name = "tour_booked" if j == 0 else "message_sent"
            ev_payload = {
                "property_id": str(prop),
                "prospect_id": str(prid),
                "event": ev_name,
                "timestamp": ev_time.isoformat(),
                "lead_source": "website",
                "metadata": {"channel": "web"},
                "ext_event_id": f"demo-{prid[:8]}-{j}",
                "ignore": False,
                "ignore_dev": False,
                "cms_id": str(uuid.uuid4()),
            }
            client.table("prospect_events").insert(ev_payload).execute()

        if i % 2 == 0:
            st = now - timedelta(hours=min(167, (i * 2 + 1) % 120))
            en = st + timedelta(minutes=45)
            bid = str(uuid.uuid4())
            client.table("bookings").insert(
                {
                    "id": bid,
                    "floorplan_id": fp,
                    "start_time": st.isoformat(),
                    "end_time": en.isoformat(),
                    "profile_id": str(prid),
                    "string_profile_id": str(prid),
                    "phone": f"+1555{i:07d}",
                    "name": f"{fn} {ln}",
                    "pin": {},
                    "qr_code": {},
                    "stratis_meta": {"source": "leads_seed"},
                    "completion_state": {"state": "completed"},
                    "utm_source": "seed",
                    "utm_medium": "leads",
                    "utm_campaign": "demo",
                    "utm_content": str(i),
                    "utm_term": "pipeline",
                    "status": "booked",
                }
            ).execute()

    return len(ids)
