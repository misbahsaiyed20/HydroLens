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
- `GET /api/reports/{report_id}/evidence` — evidence-fusion engine: finds
  related nearby/recent reports, compares against a location baseline, and
  returns a deterministic, explainable confidence assessment. See
  "Evidence fusion (Sprint 3)" below.

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

## Evidence fusion (Sprint 3)

`GET /api/reports/{report_id}/evidence` fuses a report with nearby/recent
reports and a location baseline into an explainable confidence assessment.
It never diagnoses or predicts outbreaks — only "environmental anomaly
confidence" with human officer verification as the recommended action.

**Related-report detection** (`related_report_service.py`): other
`ANALYZED` reports within `RELATED_REPORT_RADIUS_METERS` (default 300m,
haversine distance, stdlib `math` only) and
`RELATED_REPORT_TIME_WINDOW_MINUTES` (default 120min, either direction) of
the report being evaluated. `stream_name` match is attached as metadata
(`same_stream_name`) but doesn't affect the score yet — see limitations.

**Baseline** (`baseline_service.py`): the most common (mode) historical
value per indicator, from *historical* reports at that location — meaning
reports older than the current related-report time window, so the baseline
can never be built from the very reports currently being scored as
evidence (that would be circular). Needs at least
`BASELINE_MINIMUM_OBSERVATIONS` (default 5) historical reports or
`baseline.available = False` — never treated as "abnormal" by default.

**Confidence scoring** (`confidence_service.py`) — deterministic, weighted
sum of 6 sub-scores, each normalized to 0.0-1.0:

| Component | Weight | What it measures |
|---|---|---|
| Corroboration | 30% | count of agreeing nearby reports, saturating at `CORROBORATION_SATURATION_COUNT` (4) to avoid rewarding duplicate spam |
| Recency | 15% | how fresh the report + its corroborators are, relative to the time window |
| Geographic consistency | 15% | how tightly corroborating reports cluster around this one |
| Indicator agreement | 15% | fraction (not count) of nearby reports that agree — penalizes noisy/conflicting sets |
| Image quality | 10% | average Gemini-reported image quality of this report + corroborators |
| Baseline deviation | 15% | 1.0 only if a baseline exists AND this report deviates from it; 0.0 otherwise (including when no baseline exists) |

`confidence_level`: `HIGH` if score >= `CONFIDENCE_HIGH_THRESHOLD` (0.70),
`MODERATE` if >= `CONFIDENCE_MODERATE_THRESHOLD` (0.40), else `LOW`. A
**conflict safety cap** additionally forces `HIGH` down to `MODERATE`
whenever conflicting reports are at least as numerous as supporting ones,
even if the raw weighted score alone would clear the threshold.

**Evidence fusion** (`evidence_fusion_service.py`): orchestrates the above,
classifies related reports as `supporting` or `conflicting` based on
whether they agree with the evaluated report's anomaly signal, and returns
`condition_summary` / `evidence_reasons` / `recommended_action` - the last
is always either "Officer verification recommended." or "Continue
monitoring...", never an automatic decision.

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

## Known limitations (Sprint 1 + 2 + 3)

- No location dedup — every report creates a new `Location` row, even at
  identical coordinates. Related-report/baseline queries compensate for
  this via radius search rather than requiring a shared `location_id`.
- No authentication — reports are anonymous (`user_id` is nullable).
- Local disk storage only — not suitable for production/multi-instance
  deployment.
- `create_all()` schema management, not Alembic migrations.
- If Gemini analysis fails, the report silently reverts to `SUBMITTED` —
  there's no retry endpoint yet.
- The Gemini call itself was not tested live in this build environment (no
  network egress here) — verified structurally + with a mocked HTTP layer.
- **Evidence-fusion independence limitation**: there's no reporter identity
  or source verification, so "corroboration" currently just counts report
  rows near each other in space/time — it cannot distinguish five reports
  from five different people from five re-submissions by one person.
  `corroboration_score` saturates at `CORROBORATION_SATURATION_COUNT` (4)
  reports specifically to avoid rewarding duplicate spam with unbounded
  score growth, but this is a mitigation, not a real independence check.
- **Sparse baseline**: locations with fewer than `BASELINE_MINIMUM_OBSERVATIONS`
  (5) historical analyzed reports get `baseline.available = False`, and the
  scoring formula treats that as neutral (contributes 0, not a penalty or
  bonus) — but it does mean confidence for newly-monitored locations relies
  more heavily on corroboration/recency/geography than baseline deviation.
- **No verified-authority labels yet**: officer verification/dismissal
  isn't implemented (that's the next sprint), so there's no ground-truth
  feedback loop into the scoring yet.
- **Simplified environmental interpretation**: `is_abnormal()` is a coarse
  boolean gate (any indicator elevated → abnormal). It doesn't yet weigh
  which indicator is more environmentally significant than another, or
  handle partial/ambiguous indicator combinations beyond what's in
  `evidence_reasons`.
- `stream_name` match is surfaced as informational metadata
  (`same_stream_name` on related reports) but does not yet affect the
  score — left as a documented decision rather than an ad-hoc bonus term
  bolted onto the weighted formula.

## Next sprint recommendation

**Sprint 4: case creation + officer review.** Now that individual reports
can be scored, group related+corroborating reports into a persisted `Case`
(spec's `case_service`), expose it to an `officer_service` for
verify/dismiss/request-more-evidence actions, and start feeding those
verified/dismissed outcomes back as a signal for future confidence scoring.
This is also the natural point to revisit reporter-independence handling,
since a persisted Case is where "how many *independent* people reported
this" starts to matter for real.
