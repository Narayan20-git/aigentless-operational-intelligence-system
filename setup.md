# Local development setup

This guide helps a new developer run **aigentless-operational-intelligence-system** on their machine: Python environment, MongoDB, environment variables, and the FastAPI server.

---

## 1. What you need installed

| Requirement | Notes |
|-------------|--------|
| **Python 3.11+** | 3.12 is fine. Check: `python --version` |
| **Git** | To clone the repository |
| **Docker Desktop** (optional) | Only if you want MongoDB in a container instead of Atlas/local install |

---

## 2. Clone the repository

```powershell
git clone <repository-url>
cd aigentless-operational-intelligence-system
```

---

## 3. Create a virtual environment

From the project root:

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If activation fails with a script policy error:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Without activating** (works the same for commands):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 4. Install Python dependencies

With the venv activated:

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

Main stack: **FastAPI**, **Uvicorn**, **Beanie**, **PyMongo** (async), **Motor** (listed for compatibility), **python-dotenv**, **Pydantic v2**, **certifi**, **fastapi-standalone-docs** (Swagger without CDN).

---

## 5. Environment variables (`.env`)

1. In the **project root**, create a file named **`.env`** (it is **gitignored** — do not commit secrets).
2. Add at least:

```env
MONGO_URL=mongodb://127.0.0.1:27017
DB_NAME=aigentless
```

| Variable | Required | Description |
|----------|----------|-------------|
| `MONGO_URL` | Recommended | MongoDB connection string. Defaults in code to `mongodb://localhost:27017` if unset. |
| `DB_NAME` | Recommended | Database name. Defaults to `aigentless`. |

### Optional — MongoDB Atlas or strict TLS

| Variable | When to use |
|----------|-------------|
| `MONGO_TLS_RELAXED=true` | Atlas TLS fails on corporate VPN / Windows (dev only). |
| `MONGO_TLS_ALLOW_INVALID_CERTS=true` | Relax certificate validation (avoid combining with conflicting URI options). |
| `MONGO_TLS_DISABLE_OCSP=true` | OCSP checks blocked on your network. |
| `MONGO_SERVER_SELECTION_TIMEOUT_MS` | Default `10000`. Increase if slow networks. |
| `DB_OPTIONAL_STARTUP=true` | If Mongo is down, the API still starts; `/leads/*` returns **503** until DB works. |

### Example — MongoDB Atlas

```env
MONGO_URL=mongodb+srv://USER:PASSWORD@CLUSTER.mongodb.net/?retryWrites=true&w=majority
DB_NAME=aigentless
```

Ensure **Atlas → Network Access** allows your IP.

---

## 6. Run MongoDB

Pick **one** of these.

### Option A — Docker (simplest for local dev)

From the project root:

```powershell
docker compose up -d mongo
```

This starts **MongoDB 6** on **`localhost:27017`**. Use:

```env
MONGO_URL=mongodb://127.0.0.1:27017
DB_NAME=aigentless
```

### Option B — MongoDB installed on the OS

Install MongoDB Community Server, start the service, and keep `MONGO_URL` pointing at `mongodb://127.0.0.1:27017` (or your port).

### Option C — MongoDB Atlas only

Set `MONGO_URL` to your Atlas SRV string and `DB_NAME` as in Atlas. If TLS errors appear on your network, see optional env vars above or use **Option A** for local development.

---

## 7. Seed sample data (optional)

With MongoDB running and `.env` configured:

```powershell
python scripts/seed_leads.py
```

You should see a success message about **5** leads inserted into the **`leads`** collection.

---

## 8. Start the API server

From the project root, with venv activated:

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Or:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)  
- **OpenAPI JSON:** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

### Useful endpoints to verify

| Endpoint | Purpose |
|----------|---------|
| `GET /leads/summary` | UI-ready lead counts + card payload |
| `GET /leads/` | All leads |
| `GET /leads/?status=Hot` | Filter by status |
| `POST /leads/` | Create a lead |
| `GET /properties/` | Properties (stub service) |

---

## 9. Run with Docker (API + Mongo)

The repo includes `docker-compose.yml` with `api` and `mongo`. The **`Dockerfile`** must use a valid **JSON-array** `CMD` for Uvicorn, for example:

```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

If the `CMD` line uses single quotes, Docker may reject it — fix to double quotes as above.

For the **API** container to reach Mongo, set `MONGO_URL` to host **`mongo`** (the Compose service name), e.g. `mongodb://mongo:27017`, via env or compose `environment:` — not `127.0.0.1`.

---

## 10. Project layout (high level)

```
├── main.py                 # FastAPI app, lifespan, CORS, routers
├── config/database.py      # PyMongo async client, Beanie init, TLS helpers
├── models/                 # Beanie documents (User, Lead)
├── schemas/                # Pydantic request/response models
├── routes/                 # API routers (properties, leads, …)
├── services/               # Business logic
├── scripts/seed_leads.py     # Seed dummy leads
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── .env                    # Local only — create yourself, never commit
```

---

## 11. Troubleshooting

| Issue | What to try |
|-------|-------------|
| `Activate.ps1` not found | Recreate venv: `python -m venv .venv --clear` then `pip install -r requirements.txt`. |
| Mongo connection / TLS errors to Atlas | Use local Mongo (`docker compose up -d mongo`) + `MONGO_URL=mongodb://127.0.0.1:27017`; or try `MONGO_TLS_RELAXED=true` (dev only); or another network (e.g. hotspot). |
| App starts but `/leads` returns **503** | `DB_OPTIONAL_STARTUP=true` with failed DB, or Mongo not running. Fix `MONGO_URL` and restart. |
| `No module named 'beanie'` | Activate `.venv` and run `pip install -r requirements.txt`. |
| Swagger UI never loads in browser | Open `/docs` (not `/` alone). This project uses **offline** docs (`fastapi-standalone-docs`) to avoid CDN blocks. |
| CORS errors from a frontend | `main.py` allows `*` origins; tighten `allow_origins` for production. |

---

## 12. Security reminders for contributors

- **Never commit `.env`** — it is listed in `.gitignore`.
- Share **example** values in chat or a template file **without** real passwords (e.g. `MONGO_URL=mongodb+srv://USER:PASS@...` with placeholders).
- Rotate Atlas credentials if they were ever exposed.

---

## 13. Quick checklist

- [ ] Python 3.11+ installed  
- [ ] Repo cloned  
- [ ] `.venv` created and `pip install -r requirements.txt`  
- [ ] `.env` created with `MONGO_URL` and `DB_NAME`  
- [ ] MongoDB running (Docker or Atlas or local)  
- [ ] `python scripts/seed_leads.py` (optional)  
- [ ] `uvicorn main:app --reload` and open `/docs`  

You are ready to develop.
