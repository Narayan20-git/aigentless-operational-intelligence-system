"""
Upsert dashboard_home_ui.default from services/data/home_ui_default.json.

Run from repo root (requires SUPABASE_URL + service key in .env):
  python scripts/seed_dashboard_home_ui.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

DATA = ROOT / "services" / "data" / "home_ui_default.json"


def main() -> None:
    from supabase import create_client
    import os

    url = os.getenv("SUPABASE_URL", "").strip()
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip() or os.getenv("SUPABASE_KEY", "").strip())
    if not url or not key:
        raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env")
    copy_json = json.loads(DATA.read_text(encoding="utf-8"))
    client = create_client(url, key)
    client.table("dashboard_home_ui").upsert({"id": "default", "copy_json": copy_json}).execute()
    print("Upserted dashboard_home_ui id=default from home_ui_default.json")


if __name__ == "__main__":
    main()
