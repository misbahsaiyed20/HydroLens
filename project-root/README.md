# Aqua Sentinel

**A personal AI/ML environmental intelligence project.**

## Overview

Citizens submit geo-tagged photos of local streams. AI vision extracts
observable environmental indicators from each photo. Evidence fusion
cross-checks nearby/recent reports against each other and against a
location's historical baseline, producing an explainable confidence score.
A deterministic actionability layer turns that into an operational
recommendation and an exposure-risk signal. Nothing is treated as ground
truth until a human reviews it — verification and a full audit trail sit
on top of every stage. A dashboard exposes all of this as a usable
case-management interface.

## Problem

Individual citizen photo reports of environmental conditions are
inherently noisy: one photo can be misleading, mistimed, low-quality, or
simply wrong. Treating any single AI-labeled photo as fact is not
scientifically defensible. At the same time, ignoring citizen reports
because they're imperfect throws away real signal.

## Solution

Aqua Sentinel's core idea: **don't ask "what does this one photo show?" —
ask "what can we trust when multiple people observe the same environment
differently?"** Corroboration, disagreement, recency, geographic
clustering, and deviation from a location's own history all feed into one
explainable confidence score — never a black box, and never a medical or
outbreak claim. A human still makes the final call.

## Core workflow

```
Citizen submits report (photo + location)
        |
        v
AI vision observation (Gemini) — algae, turbidity, waste, color, quality
        |
        v
Evidence fusion — related reports (geo + time) + historical baseline
        |
        v
Confidence score (deterministic, weighted, explainable)
        |
        v
Actionability — exposure-risk signal + recommended review action
        |
        v
Human verification — VERIFIED / REJECTED, with an audit trail
        |
        v
FHIR-compatible representation + dashboard / case-management view
```

Mermaid version (renders on GitHub):

```mermaid
flowchart TD
    A[Citizen] --> B[Report: photo + location]
    B --> C[AI Observation - Gemini vision]
    C --> D[Evidence Fusion]
    D --> E[Baseline + Context]
    E --> F[Confidence Score]
    F --> G[Actionability + Exposure Risk]
    G --> H[Human Verification]
    H --> I[Audit Trail / FHIR]
    I --> J[Dashboard / Case Management]
```

## Architecture

```
backend/            FastAPI + SQLAlchemy + PostgreSQL
  app/
    models/          Report, Location, Observation, VerificationEvent, enums
    schemas/          Pydantic request/response schemas
    api/              reports, dashboard, cases routers
    services/         one file per concern — vision, analysis, related-report
                       detection, baseline, confidence, actionability,
                       exposure-risk, evidence-fusion orchestration, FHIR,
                       verification, dashboard/case aggregation, storage
  alembic/            schema migrations (Sprint 7)
  evaluation/         labeled evaluation dataset + harness (Sprint 7)
  tests/              153+ tests, pytest, SQLite in-memory, Gemini mocked

frontend/            Next.js 14 + TypeScript + Tailwind
  app/                report form, dashboard, case list, case detail
  components/         ui/, dashboard/, cases/, evidence/, map/
  lib/                typed API client
```

## Technology stack

- **Backend**: Python, FastAPI, SQLAlchemy, Pydantic, PostgreSQL (SQLite in tests)
- **AI**: Google Gemini vision, called through one isolated service (`vision_service.py`)
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Migrations**: Alembic (Sprint 7)
- **Testing**: pytest (backend), `next build` (frontend) — no live AI calls in tests, ever

## AI observation pipeline

`POST /api/reports` returns immediately (`status: SUBMITTED`); a background
task then calls Gemini (`vision_service.py`), moving the report through
`ANALYZING` -> `ANALYZED`. The model returns exactly six fields: algae
indicator, turbidity indicator, visible waste, color anomaly, image
quality, and its own confidence — never a diagnosis, never a risk verdict.

**Sprint 7 hardening**: every response is schema-validated
(`_validate_indicators`) before it's ever written to the database — wrong
enum values, wrong types, out-of-range confidence, or missing fields are
all rejected. On any failure (bad key, network error, malformed/invalid
response), the report reverts to `SUBMITTED` rather than getting stuck or
persisting garbage — it's retriable, and nothing invented is saved.

## Dashboard / case management (Sprint 6-7)

There's no separate `Case` database table — a "case" is simply an
`ANALYZED` report viewed through its evidence-fusion + actionability +
verification results, computed live via the existing services (no
duplicated logic).

- `GET /api/dashboard/summary` — live counts: total reports, pending AI
  review, analyzed, high-confidence, verified, rejected, needs-review
- `GET /api/cases` — filterable list (confidence level, exposure risk,
  action level, verification status, date range, location radius)
- `GET /api/cases/{id}` — full case detail: signal summary, supporting/
  conflicting evidence with provenance, baseline, evidence reasons,
  verification history, and a pointer to the FHIR view

Frontend: `/dashboard` (summary cards), `/cases` (filterable list + a
lightweight SVG scatter map — no external map dependency was added for
this project's scale), `/cases/[id]` (full case detail with an evidence
timeline). Labeled a development/officer workflow — there is no
authentication system yet (see Limitations).

## Evaluation methodology (Sprint 7)

Two small, clearly-scoped internal evaluations — **not** statistically
representative benchmarks:

- **AI observation evaluation** (`evaluation/`): 8 hand-labeled, synthetic
  scenarios (normal / unusual color / algae-like / visible waste / turbid
  / mixed-conflicting / weak evidence / strong corroborating). No real
  photos ship with this repo and no live Gemini calls are made
  automatically — `run_evaluation()` accepts real image paths for a real
  run (requires a `GEMINI_API_KEY` and real photos, neither provided
  here), and is exercised in `tests/test_evaluation.py` with a mocked
  model response purely to verify the comparison/metrics logic itself is
  correct and deterministic.
- **Evidence-fusion evaluation** (`tests/test_evaluation_evidence_scenarios.py`):
  8 deterministic scenarios (isolated report, agreeing reports,
  conflicting reports, baseline deviation, insufficient baseline, verified
  evidence, rejected evidence, mixed provenance) proving confidence/
  actionability behavior is stable and matches the documented rules.

No accuracy percentage is reported anywhere in this project — an 8-item
synthetic set cannot support one honestly.

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

## Actionability + exposure risk (Sprint 4)

Two new endpoints turn the Sprint 3 evidence-fusion result into something an
officer can actually act on, without ever crossing into medical territory.
The pipeline is strictly one-directional and each stage only reads the
previous stage's output:

```
ENVIRONMENTAL OBSERVATION -> EVIDENCE FUSION -> CONFIDENCE
    -> EXPOSURE-RISK SIGNAL -> OPERATIONAL REVIEW ACTION
```

It never becomes `OBSERVATION -> DIAGNOSIS` or `OBSERVATION -> OUTBREAK
PREDICTION` at any point — there is no code path that produces disease
names, outbreak claims, or confirmed-contamination language, and this is
enforced by test (`test_no_medical_language_in_reasons`).

**`GET /api/reports/{report_id}/actionability`** (`actionability_service.py`)
does NOT recompute confidence — `confidence_service` (Sprint 3) remains the
sole authority for that. It only interprets the existing
`EvidenceFusionResult` (extended this sprint with an `indicator_severity`
field — NONE/LOW/MODERATE/HIGH, from `indicator_scales.get_indicator_severity`)
into one of three action levels, first-matching-rule wins:

1. `confidence_level == LOW` or `indicator_severity == NONE` -> `CONTINUE_MONITORING`
2. `confidence_level == HIGH` AND conflicting < supporting AND
   (`indicator_severity == HIGH` OR `supporting >= PRIORITY_REVIEW_MIN_SUPPORTING_COUNT` (3))
   -> `PRIORITY_REVIEW`
3. otherwise -> `REVIEW_RECOMMENDED`

Same principle as Sprint 3's conflict cap: a report can only reach
`PRIORITY_REVIEW` when supporting evidence clearly outweighs conflicting
evidence, never by simple majority.

The **exposure-risk signal** (`exposure_risk_service.py`) answers a
deliberately narrow question: does this observation, combined with how much
corroborated evidence supports it, look worth flagging for environmental/
public-health review if people might interact with the water? It says
nothing about who is exposed or what illness could result. Deterministic
lookup table (`indicator_severity` x `confidence_level`), then a one-level
bump (capped at ELEVATED) if the location's baseline is available and
deviates:

| | LOW conf | MODERATE conf | HIGH conf |
|---|---|---|---|
| **NONE** | LOW | LOW | LOW |
| **LOW** | LOW | LOW | MODERATE |
| **MODERATE** | LOW | MODERATE | ELEVATED |
| **HIGH** | MODERATE | ELEVATED | ELEVATED |

Example response:

```json
{
  "confidence_score": 0.717,
  "confidence_level": "HIGH",
  "exposure_risk_level": "ELEVATED",
  "action_level": "PRIORITY_REVIEW",
  "recommended_action": "Priority environmental officer review recommended — strong, corroborated evidence of an anomaly.",
  "key_reasons": ["3 corroborating observation(s) within 300m / 120 minutes", "..."],
  "supporting_report_count": 3,
  "conflicting_report_count": 1,
  "baseline": { "available": true, "deviates": true }
}
```

## FHIR interoperability (Sprint 4)

**`GET /api/reports/{report_id}/fhir`** (`fhir_service.py`) returns a
FHIR R4-shaped `Observation` resource — not a FHIR server, no validation
against the full spec, no persistence. Isolated in one module so nothing
else in the app is coupled to FHIR structure.

Deliberate choices, all in the "do not fabricate data" spirit:

- **`subject` references an environmental location, not a Patient**
  (`{"display": "Stream location (lat, lon) — stream name"}`) — FHIR's base
  Observation resource explicitly allows non-Patient subjects, and this is
  an environmental observation, not a clinical one. No `reference` id is
  invented, only a display string built from real data.
- **`status` is always `"preliminary"`**, never `"final"` — there is no
  human/officer verification step yet (that's a later sprint), and FHIR's
  own definition of "preliminary" (initial/interim, may be unverified) is
  the honest description of AI-extracted, un-reviewed data.
- **No LOINC/SNOMED codes are invented.** Every `code`/`component.code`
  uses free-text `CodeableConcept.text` rather than a fabricated coding
  system this project hasn't validated against a terminology server.
- **No patient demographic fields exist anywhere in the resource** — there
  is nothing to map, so nothing is invented to fill the gap.
- Environmental indicators (turbidity, algae, visible waste, color
  anomaly, image quality, model confidence) plus evidence-fusion confidence
  score/level/related-report-count are represented as `component` entries;
  `note` carries the human-readable `condition_summary`.

## Trust architecture (Sprint 5)

The central principle of this sprint: **AI-generated observations are not
automatically ground truth.** Aqua Sentinel keeps a strict, explicit
pipeline:

```
AI OBSERVATION -> EVIDENCE FUSION -> CONFIDENCE
    -> HUMAN VERIFICATION -> VERIFIED ENVIRONMENTAL RECORD
```

Two states are tracked on every report, and they answer two different
questions:

| | Question it answers | Field | Values |
|---|---|---|---|
| **AI status** | "Has the image been analyzed?" | `Report.status` | SUBMITTED / ANALYZING / ANALYZED / ... |
| **Verification status** | "Has a human reviewed/confirmed this observation?" | `Report.verification_status` | UNVERIFIED / VERIFIED / REJECTED |

These are never conflated. A report can be `ANALYZED` (AI finished) while
still `UNVERIFIED` (no human has looked at it) — that's the default and
expected state for almost every report in this system. Nothing in the AI
pipeline (`analysis_service.py`) ever sets `verification_status`; only a
`POST /verify` call does.

### AI observation vs. human verification

These are two distinct, separately-stored pieces of data and the API never
merges them:

```json
// AI observation (Observation row, Sprint 2 — untouched by verification)
{ "algae_indicator": "high", "color_anomaly": "bright green", "model_confidence": 0.95 }

// Human verification (VerificationEvent row, Sprint 5 — separate table)
{ "verification_status": "VERIFIED", "verifier_reference": "reviewer_1", "verified_at": "...", "note": "..." }
```

`model_confidence` (how confident the Gemini vision model was in its own
reading) and `verification_status`/history (whether a human agreed with
that reading) are never merged into one field. There is deliberately no
`verification_confidence` field — verification is a discrete human
decision (VERIFIED/REJECTED), not a second confidence score.

### Verification lifecycle

1. Report is created -> `verification_status = UNVERIFIED` (default, always)
2. Report finishes AI analysis (`status = ANALYZED`)
3. A person calls `POST /api/reports/{id}/verify` with `VERIFIED` or
   `REJECTED`, a `verifier_reference`, and an optional `note`
4. `verification_service.py` validates the report exists and is
   `ANALYZED`, writes an immutable `VerificationEvent` row (capturing the
   previous status, new status, verifier, note, timestamp), and updates
   `Report.verification_status` — the AI `Observation` row is never
   touched
5. `GET /api/reports/{id}/verification` returns the current status plus
   the full history of every verification action taken

`verifier_reference` is a **plain string**, not an authenticated identity —
there is no login/auth system in this project yet. It exists so the
architecture has a place for a real authenticated user reference once auth
is added, without pretending that authentication already exists. No real
officer identities are fabricated anywhere in this codebase or its tests.

### Audit trail

Every verification action produces one `VerificationEvent` row:
`event_type`, `report_id`, `previous_status`, `new_status`,
`verifier_reference`, `note`, `created_at`. Rows are **append-only** —
never updated after creation, so `created_at` is the only timestamp (no
`updated_at`, since that would misleadingly imply rows can change). This
one table intentionally serves as both the "verification record" and the
"audit trail" — they turned out to need identical fields, so a second
table would just be a copy of the first.

### Evidence provenance

`GET /api/reports/{id}/evidence` now includes an `evidence_provenance`
object breaking supporting/conflicting related reports down by
verification status (`supporting_verified_count`,
`supporting_unverified_count`, `supporting_rejected_count`, and the
conflicting-side equivalents), plus each individual related report's
`verification_status`. `evidence_reasons` gets plain-language additions
like *"2 supporting reports are human-verified"* or *"supporting evidence
is currently unverified"*.

**This is purely descriptive — `confidence_service.py`'s scoring formula
was not touched** (verified by an empty `git diff` on that file, and by a
test asserting two otherwise-identical evidence sets score identically
regardless of verification status). Verification status does not inflate
or deflate the confidence score in this sprint. REJECTED reports are
**not** excluded from the supporting/conflicting sets computed in Sprint 3
— excluding them would silently change confidence_service's inputs, which
this sprint deliberately avoids. They're flagged in the provenance
breakdown and reasons instead ("should be weighed cautiously"), not
removed from the evidence pool. A future sprint could reasonably choose to
exclude REJECTED reports from scoring — that's a real design decision
requiring its own justification, not something to slip in as a side effect
of adding provenance.

### FHIR implications

`fhir_service.py`'s `status` field now reflects verification, still without
overclaiming:

| `verification_status` | FHIR `status` | Why |
|---|---|---|
| UNVERIFIED | `preliminary` | FHIR's own definition: initial/interim, may be unverified — an honest description of AI-only, unreviewed data |
| VERIFIED | `final` | FHIR's own definition: "complete, no further action needed" — a statement about the *data's review status*, not a claim the environmental condition is scientifically proven |
| REJECTED | `cancelled` | FHIR's own definition: "no longer valid, should not be used for any purpose" — matches a human reviewer determining the observation shouldn't count as evidence. The underlying report/photo still exists; only its evidentiary status changes. |

**Human verification does not equal medical or scientific certainty.**
"Final" in FHIR terms means a person reviewed and accepted this
*environmental observation* as a reasonable read of a photo — it is not a
laboratory result, not a certified water-quality test, and not a medical
finding. The verifier's identity is deliberately **excluded** from the
FHIR resource itself (only the non-identifying status + timestamp appear)
to avoid embedding personal information into an interoperability payload.

## Local setup

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL, GEMINI_API_KEY

# fresh database (no tables yet):
alembic upgrade head

# OR, if this DB already has tables from an EARLIER create_all() run
# THAT PREDATES AUTHENTICATION (Sprint 1-7, before password_hash/role
# existed) — two steps, not one:
alembic stamp e829fbc64e49   # mark the DB as being at the initial-schema revision, matching its real (pre-auth) tables
alembic upgrade head         # now actually run every migration after that — adds password_hash/role to users
# Running `alembic stamp head` alone here is a real trap: stamp only
# records version history, it never executes a migration's DDL. Stamping
# straight to head marks the DB as "fully migrated" while password_hash/
# role were never actually added — the exact cause of a
# "column users.password_hash does not exist" error at signup.

# OR, if this DB already has ALL current tables including auth
# (e.g. restored from a backup that already ran both migrations):
alembic stamp head           # single step is correct here — the columns already exist

uvicorn app.main:app --reload
```
API docs (development only): http://localhost:8000/docs · Health: http://localhost:8000/health

To call protected endpoints from Swagger: click **Authorize**, and paste
**only the raw token** (e.g. `eyJhbGc...`) into the value box — do not
type `Bearer <token>`. Swagger UI adds the `Bearer ` prefix itself; typing
it yourself sends `Authorization: Bearer Bearer <token>`, which the server
correctly rejects as an invalid token (401, not a crash) but is a common
point of confusion.

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```
http://localhost:3000 — citizen report form; http://localhost:3000/dashboard — case dashboard.

### Testing

```bash
cd backend && pytest -v     # 153+ tests, SQLite, Gemini always mocked
cd frontend && npm run build
```

## Environment variables

**Backend** (`backend/.env`):

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | Postgres connection string | `postgresql+psycopg2://postgres:postgres@localhost:5432/aqua_sentinel` |
| `ENVIRONMENT` | `development` / `production` — controls `/docs` availability | `development` |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins | `http://localhost:3000` |
| `UPLOAD_DIR` | Local image storage folder | `uploads` |
| `MAX_UPLOAD_SIZE_MB` | Max image size | `8` |
| `GEMINI_API_KEY` | Gemini API key — server-side only, never sent to the frontend | *(required for AI analysis)* |
| `GEMINI_MODEL` | Gemini model | `gemini-3.5-flash` |
| `RELATED_REPORT_RADIUS_METERS` / `RELATED_REPORT_TIME_WINDOW_MINUTES` | Related-report matching window | `300.0` / `120` |
| `BASELINE_MINIMUM_OBSERVATIONS` | Min. historical reports for a baseline | `5` |
| `CORROBORATION_SATURATION_COUNT` | Report count where corroboration score maxes out (duplicate-safety mitigation) | `4` |
| `CONFIDENCE_HIGH_THRESHOLD` / `CONFIDENCE_MODERATE_THRESHOLD` | Confidence level cutoffs | `0.70` / `0.40` |
| `PRIORITY_REVIEW_MIN_SUPPORTING_COUNT` | Min. supporters for PRIORITY_REVIEW | `3` |

**Frontend** (`frontend/.env.local`): `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000/api`) — the only frontend env var; it is a URL, never a secret. No API key of any kind is ever exposed to the browser.

## Deployment readiness

- **Backend**: set env vars above, provision PostgreSQL, run `alembic
  upgrade head` (fresh DB) or `alembic stamp head` (existing create_all()
  DB), start with `uvicorn app.main:app --host 0.0.0.0 --port 8000`
  (behind a real ASGI server config / reverse proxy for production —
  `--reload` is dev-only). Set `ENVIRONMENT=production` to disable
  `/docs`/`/redoc`.
- **Uploads**: local disk (`uploads/`) is dev-only — doesn't survive
  container restarts or scale across multiple instances. Swap
  `storage_service.py` for S3/GCS before any real multi-instance
  deployment; it's isolated behind one small function for exactly this.
- **Frontend**: `npm run build && npm start`, or any static/Node host;
  set `NEXT_PUBLIC_API_BASE_URL` to the deployed backend URL at build time
  (Next.js inlines `NEXT_PUBLIC_*` vars into the client bundle).
- **Docker**: `backend/Dockerfile`, `frontend/Dockerfile`, and a root
  `docker-compose.yml` (Postgres + backend + frontend) are provided for
  local reproducibility. **Not build-tested** in the environment this was
  written in (no Docker daemon available there) — reviewed by hand against
  `requirements.txt`/`package.json`/the app's actual startup path, but run
  `docker compose up --build` yourself before relying on it. No
  Kubernetes/microservices — unnecessary complexity for a personal project
  at this scale.

## Limitations

- **No authentication** — the dashboard is a development/officer workflow
  with no login; `verifier_reference` is an unauthenticated free-text
  string, not a real identity.
- **Duplicate/spam reports**: no identity-based fraud detection exists.
  The only mitigation is `CORROBORATION_SATURATION_COUNT` — confidence
  scoring caps out at N agreeing reports rather than scaling unboundedly
  with duplicate submissions, but this cannot distinguish independent
  reporters from one person resubmitting. Documented, not solved.
- **No caching/precomputation** — dashboard/case-list filtering recomputes
  evidence fusion per analyzed report on every request. Fine at personal-
  project scale; would need persisted/cached confidence scores at real
  volume.
- **Map is a schematic SVG scatter plot**, not a real geographic basemap
  (no Leaflet/Mapbox dependency added — see `components/map/CaseMap.tsx`
  for the tradeoff).
- **FHIR output is one-way and in-memory** — not a compliant FHIR server,
  no persistence, no round-trip import, no terminology validation.
- **Verification doesn't feed back into scoring** — `confidence_service`'s
  formula is untouched by verification status; provenance is exposed
  descriptively only (deliberate, see Evidence Fusion section).
- **Evaluation is illustrative, not a benchmark** — 8 synthetic scenarios
  each for AI observation and evidence-fusion evaluation; no claim of
  statistical representativeness.
- **create_all() still runs on every backend startup** alongside Alembic
  (harmless once tables exist) — full migration-only discipline would mean
  removing this, left as-is for local dev convenience.

## Future improvements

- Real authentication + accountable verifier identity
- Persisted `Case` model grouping reports, enabling a verified-outcome
  feedback loop into confidence scoring
- Cached/precomputed confidence scores for dashboard performance at scale
- Real interactive map (Leaflet + OpenStreetMap)
- Object storage (S3/GCS) for uploaded images
- A larger, more rigorous evaluation set with real labeled photos
