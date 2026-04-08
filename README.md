# Aigentless POC — Property Onboarding Backend

## Stack
- **Database**: Supabase (PostgreSQL + pgvector)
- **Backend**: Python + FastAPI
- **AI**: Google Gemini (via Google ADK)
- **Embeddings**: Google text-embedding-004 → Supabase pgvector

---

## Setup — Step by Step

### Step 1 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Configure environment
```bash
cp .env.example .env
# Edit .env with your Supabase URL, Service Role Key, Google API Key
```

### Step 3 — Run migration in Supabase SQL Editor
```
Supabase Dashboard → SQL Editor → New Query
Paste: migration_category2.sql → Run
Then: setup_pgvector.sql → Run
```

### Step 4 — Seed dummy data
```
Supabase Dashboard → SQL Editor → New Query
Paste: seed_data.sql → Run
```

### Step 5 — Generate embeddings (optional but recommended for RAG)
```bash
python generate_embeddings.py
```

### Step 6 — Start FastAPI server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Step 7 — View Swagger docs
```
http://localhost:8000/docs
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/onboarding/summary` | KPI cards (ready/blocked/in-progress/avg%) |
| GET | `/api/v1/onboarding` | All properties with onboarding status |
| GET | `/api/v1/onboarding?property_id=` | Filter by property |
| GET | `/api/v1/onboarding?status=blocked` | Filter by status |
| GET | `/api/v1/onboarding/{id}` | Property detail + 6 section scores + blockers |
| GET | `/api/v1/onboarding/{id}/checklist` | Full checklist all sections |
| GET | `/api/v1/onboarding/{id}/checklist/{section}` | Single section checklist |
| POST | `/api/v1/onboarding/{id}/generate-content` | Generate missing content (AI) |
| GET | `/api/v1/onboarding/{id}/ai-jobs` | List AI jobs for property |
| GET | `/api/v1/onboarding/{id}/ai-jobs/{job_id}` | Single job status |

---

## Project Structure
```
aigentless/
├── main.py                     # FastAPI app entry point
├── requirements.txt
├── .env.example
├── migration_category2.sql     # Run first in Supabase
├── seed_data.sql               # Run second in Supabase
├── setup_pgvector.sql          # Run third in Supabase
├── generate_embeddings.py      # Run after seeding
└── app/
    ├── db.py                   # Supabase client
    ├── scheduler.py            # 5-min recalculation job
    └── routers/
        ├── onboarding.py       # Main onboarding endpoints
        ├── checklist.py        # View Detailed Checklist
        └── generate_content.py # Generate Missing Content (Gemini)
```

---

## Key Design Decisions
- **Completion recalculation**: FastAPI scheduler every 5 minutes
- **Required counts**: Hardcoded fixed rules (no extra config table)
- **AI generation**: Async background jobs (non-blocking)
- **RAG**: pgvector similarity search on existing FAQs/amenities
- **Embeddings**: Google text-embedding-004 (768 dimensions)
- **No RLS**: Skipped for POC simplicity
