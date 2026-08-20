# Aqua Sentinel

Citizen-driven environmental evidence and triage system for urban freshwater
ecosystems — built for the IEEE OneAquaHealth Global Hackathon 2026.

Citizens submit geo-tagged stream photos. The system does **not** diagnose
disease or predict outbreaks — it turns messy citizen observations into
explainable, human-reviewed evidence (observable environmental indicators,
exposure-risk signals, evidence confidence) that a local officer can verify
or dismiss. See project docs for the full pipeline; this repo currently
implements **Sprint 1 only**: database foundation + report submission.

## Sprint 1 scope

- PostgreSQL schema: `User`, `Location`, `Report`, `Observation`
- `POST /api/reports` — citizen submits photo + coordinates (+ optional
  stream name / description); AI vision analysis then runs in the
  background
- `GET /api/reports/{id}` — fetch a single report (poll this to see status
  move SUBMITTED → ANALYZING → ANALYZED)
- `GET /api/reports` — paginated list
- Local disk image storage (dev only — swap for S3/GCS before production)
- Anonymous reporting (no auth yet — `Report.user_id` is nullable)
- Gemini vision analysis (`image_analysis_service`) — extracts observable
  indicators (algae, color anomaly, visible waste, turbidity, image
  quality, model confidence) into the `Observation` row, isolated behind
  `vision_service.py` so swapping providers later is a one-file change

Explicitly **not** built yet: evidence fusion, baseline comparison, case
creation, officer review, FHIR export, real auth, a retry endpoint for
failed analyses. Those are later sprints.

## Project structure

```
project-root/
├── backend/           FastAPI + SQLAlchemy + PostgreSQL
│   ├── app/
│   │   ├── models/     SQLAlchemy models (User, Location, Report, Observation)
│   │   ├── schemas/    Pydantic request/response schemas
│   │   ├── api/        API routers (reports.py)
│   │   ├── services/   storage_service.py (local image storage)
│   │   ├── config.py   env-driven settings
│   │   ├── database.py engine/session setup
│   │   └── main.py     FastAPI app entrypoint
│   ├── tests/          pytest suite (SQLite, no external DB needed)
│   ├── uploads/         local image storage (dev)
│   ├── requirements.txt
│   └── .env.example
├── frontend/           Next.js 14 + TypeScript + Tailwind
│   ├── app/             App Router pages
│   ├── components/      ReportForm.tsx
│   └── .env.local.example
└── README.md
```

## Backend setup

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env — set DATABASE_URL to a real Postgres instance, e.g.:
#   postgresql+psycopg2://postgres:postgres@localhost:5432/aqua_sentinel
# make sure that database exists first: `createdb aqua_sentinel`

uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs
Health check: http://localhost:8000/health

Tables are created automatically on startup via `Base.metadata.create_all()`
— no manual migration step needed for Sprint 1. This is intentional for a
fresh project; switch to Alembic once the schema stabilizes and starts
changing incrementally.

### Run tests

```bash
cd backend
pytest -v
```

Tests run against an isolated SQLite file (not your dev Postgres DB), so
`pytest` works with zero setup.

## Frontend setup

```bash
cd frontend
npm install
cp .env.local.example .env.local
# edit .env.local if your backend isn't on localhost:8000

npm run dev
```

Open http://localhost:3000 — a form to submit a stream observation
(coordinates, optional stream name/description, required photo).

## Environment variables

**Backend** (`backend/.env`):
| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | Postgres connection string | `postgresql+psycopg2://postgres:postgres@localhost:5432/aqua_sentinel` |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins | `http://localhost:3000` |
| `UPLOAD_DIR` | Local folder for uploaded images | `uploads` |
| `MAX_UPLOAD_SIZE_MB` | Max image size | `8` |
| `GEMINI_API_KEY` | Gemini API key for vision analysis | *(required for analysis to run — get one at https://aistudio.google.com/apikey)* |
| `GEMINI_MODEL` | Gemini model to call | `gemini-3.5-flash` |

**Frontend** (`frontend/.env.local`):
| Variable | Purpose | Default |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Backend API base URL | `http://localhost:8000/api` |

## Known limitations (Sprint 1 + 2)

- No location dedup — every report creates a new `Location` row, even at
  identical coordinates. Clustering nearby points into a shared monitoring
  point belongs to `baseline_service` in a later sprint.
- No authentication — reports are anonymous (`user_id` is nullable).
- Local disk storage only — not suitable for production/multi-instance
  deployment.
- `create_all()` schema management, not Alembic migrations.
- If Gemini analysis fails (bad key, network error, unparseable response),
  the report silently reverts to `SUBMITTED` — there's no retry endpoint or
  user-facing error yet. Check server logs to see why.
- The Gemini call itself was **not** tested live in this build environment
  (no network egress to `generativelanguage.googleapis.com` here) — it was
  verified structurally (correct request/response shape against the
  documented API) and the surrounding pipeline (status transitions, DB
  writes, error handling) was tested with a mocked HTTP layer. Confirm the
  real call works once you run it with your key.

## Next sprint recommendation

**Sprint 3: evidence fusion foundations.** Now that `Observation` rows get
populated, start `evidence_fusion_service`: given a new analyzed report,
find nearby reports (`find_related_reports`) within a time/distance window
of the same location, and lay the groundwork for `baseline_service` (a
per-location baseline to compare against) and `confidence_service`
(corroboration/disagreement scoring). This is the layer the spec calls the
actual "core innovation" — worth designing carefully rather than rushing.
