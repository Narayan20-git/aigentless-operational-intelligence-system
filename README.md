# aigentless-operational-intelligence-system

## Dashboard API + Supabase bootstrap

1. Set env vars in `.env`:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY` (or `SUPABASE_KEY`)
   - `SUPABASE_DB_URL` (direct Postgres connection string for schema/data bootstrap)
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Create tables and seed data:
   - `python scripts/bootstrap_supabase.py`
4. Run API:
   - `python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000`

Available frontend-aligned endpoints:
- `GET /api/dashboard/home`
- `GET /api/leads/summary`
- `GET /api/inventory/vacant-units`
- `GET /api/properties/onboarding`
- `GET /api/portfolio/overview`
- `GET /api/briefs/weekly`
- `GET /api/integrations`
- `GET /api/profile/summary`