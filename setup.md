# Local development setup

Brief steps to go from **clone** to **running** **aigentless-operational-intelligence-system** (FastAPI + Supabase).

---

## Quick path (clone → run)

1. **Install:** Python **3.11+**, **Git**.
2. **Clone** the repo and enter the folder:

   ```powershell
   git clone https://github.com/Narayan20-git/aigentless-operational-intelligence-system.git
   cd aigentless-operational-intelligence-system
   ```

3. **Virtual environment** (Windows PowerShell):

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If activation fails (execution policy):

   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

4. **Dependencies:**

   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Environment variables:** copy `.env.example` to `.env` in the project root and set these three (same names as in Supabase **Settings → API**):

   | Variable | Notes |
   |----------|--------|
   | `SUPABASE_URL` | Project URL. |
   | `SUPABASE_KEY` | **anon / public** key (used if service role is empty). |
   | `SUPABASE_SERVICE_ROLE_KEY` | **Service role** key for backend use; takes precedence over `SUPABASE_KEY` when set. Keep secret. |

   The app resolves the API key in this order: `SUPABASE_SERVICE_ROLE_KEY` → `SUPABASE_KEY` → `SUPABASE_ANON_KEY` (optional alias). It pings the **`properties`** table on startup; ensure that table exists and RLS/policies match the key you use.

6. **Start the API:**

   ```powershell
   python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```

7. **Open:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) (Swagger). Root `/` redirects to `/docs`.

---

## Prerequisites (detail)

| Requirement | Notes |
|-------------|--------|
| **Python 3.11+** | Check: `python --version` |
| **Git** | For cloning |
| **Supabase project** | URL + API key(s) as above |

---

## macOS / Linux

```bash
git clone https://github.com/Narayan20-git/aigentless-operational-intelligence-system.git
cd aigentless-operational-intelligence-system
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
# create .env from .env.example, then:
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

---

## Without activating the venv

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

---

## Stack (reference)

- **FastAPI**, **Uvicorn**, **Pydantic v2**, **python-dotenv**, **fastapi-standalone-docs** (Swagger without CDN), **Supabase** Python client.

---

## Optional: Docker

The repo includes a `Dockerfile` and `docker-compose.yml`. The API container needs **`SUPABASE_*` variables** (e.g. `environment` or `--env-file .env`); the compose file also defines a **MongoDB** service, which the current app code does **not** use—prefer running the API locally with `.env` unless you adjust compose for your deployment.

Example build/run pattern:

```powershell
docker build -t aigentless-api .
docker run --env-file .env -p 8000:8000 aigentless-api
```

---

## Project layout (high level)

```
├── main.py                 # FastAPI app, CORS, routers
├── config/database.py      # Supabase client, startup ping
├── routes/                 # API routers (e.g. properties)
├── services/               # Business logic
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env                    # Local only — create from .env.example, never commit
```

---

## Troubleshooting

| Issue | What to try |
|-------|-------------|
| `Missing SUPABASE_URL or ...` | Fill `.env`; restart Uvicorn. |
| **503** on `/properties/*` | Supabase unreachable or ping failed; check URL, key, network, and `properties` table. |
| `Activate.ps1` not found | Recreate venv: `python -m venv .venv --clear` then reinstall requirements. |
| Swagger does not load | Use `/docs` (offline docs bundle). |

---

## Security

- Do **not** commit `.env` or real keys.
- Prefer **service role** only on the server; never expose it in frontend code.

---

## Checklist

- [ ] Python 3.11+ and Git installed  
- [ ] Repo cloned  
- [ ] `.venv` created and `pip install -r requirements.txt`  
- [ ] `.env` with `SUPABASE_URL`, `SUPABASE_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` (as in `.env.example`)  
- [ ] Supabase project has `properties` (and policies match your key)  
- [ ] `uvicorn main:app --reload` and open `/docs`  
