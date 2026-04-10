"""
Deprecated — `ui_payloads` is no longer used by the API.

Dashboard and UI routes build responses live from operational tables
(see `services/live_ui_payloads.py` and `services/dashboard_service.py`).

This script is kept only so old automation does not fail silently.
Run: `python scripts/sync_ui_payloads.py` — exits 0 with an informational message.
"""

from __future__ import annotations


def main() -> None:
    print(
        "sync_ui_payloads: no-op. The backend does not read public.ui_payloads anymore. "
        "You can DROP TABLE public.ui_payloads after verifying deployments (see sql/drop_ui_payloads.sql)."
    )


if __name__ == "__main__":
    main()
