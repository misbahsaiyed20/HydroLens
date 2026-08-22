Aqua Sentinel
Citizen-driven environmental evidence and triage system for urban freshwater
ecosystems — built for the IEEE OneAquaHealth Global Hackathon 2026.
Citizens submit geo-tagged stream photos. The system does not diagnose
disease or predict outbreaks — it turns messy citizen observations into
explainable, human-reviewed evidence (observable environmental indicators,
exposure-risk signals, evidence confidence) that a local officer can verify
or dismiss. This repo implements Sprints 1–4: database foundation +
report submission, AI vision analysis, evidence fusion, and now
actionability + FHIR-compatible interoperability.
Implemented scope (Sprints 1–4)
PostgreSQL schema: `User`, `Location`, `Report`, `Observation`
`POST /api/reports` — citizen submits photo + coordinates (+ optional
stream name / description); AI vision analysis then runs in the
background
`GET /api/reports/{id}` — fetch a single report (poll this to see status
move SUBMITTED → ANALYZING → ANALYZED)
`GET /api/reports` — paginated list
Local disk image storage (dev only — swap for S3/GCS before production)
Anonymous reporting (no auth yet — `Report.user_id` is nullable)
Gemini vision analysis (`image_analysis_service`) — extracts observable
indicators (algae, color anomaly, visible waste, turbidity, image
quality, model confidence) into the `Observation` row, isolated behind
`vision_service.py` so swapping providers later is a one-file change
`GET /api/reports/{report_id}/evidence` — evidence-fusion engine: finds
related nearby/recent reports, compares against a location baseline, and
returns a deterministic, explainable confidence assessment. See
"Evidence fusion (Sprint 3)" below.
`GET /api/reports/{report_id}/actionability` — deterministic operational
recommendation (CONTINUE_MONITORING / REVIEW_RECOMMENDED /
PRIORITY_REVIEW) plus an exposure-risk signal (LOW / MODERATE /
ELEVATED), derived from the evidence-fusion result. See "Actionability +
exposure risk (Sprint 4)" below.
`GET /api/reports/{report_id}/fhir` — FHIR-compatible Observation
resource for the report, for future interoperability. See "FHIR
interoperability (Sprint 4)" below.
Explicitly not built yet: evidence fusion, baseline comparison, case
creation, officer review, FHIR export, real auth, a retry endpoint for
failed analyses. Those are later sprints.
Project structure
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
Backend setup
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
Run tests
```bash
cd backend
pytest -v
```
Tests run against an isolated SQLite file (not your dev Postgres DB), so
`pytest` works with zero setup.
Frontend setup
```bash
cd frontend
npm install
cp .env.local.example .env.local
# edit .env.local if your backend isn't on localhost:8000

npm run dev
```
Open http://localhost:3000 — a form to submit a stream observation
(coordinates, optional stream name/description, required photo).
Evidence fusion (Sprint 3)
`GET /api/reports/{report_id}/evidence` fuses a report with nearby/recent
reports and a location baseline into an explainable confidence assessment.
It never diagnoses or predicts outbreaks — only "environmental anomaly
confidence" with human officer verification as the recommended action.
Related-report detection (`related_report_service.py`): other
`ANALYZED` reports within `RELATED_REPORT_RADIUS_METERS` (default 300m,
haversine distance, stdlib `math` only) and
`RELATED_REPORT_TIME_WINDOW_MINUTES` (default 120min, either direction) of
the report being evaluated. `stream_name` match is attached as metadata
(`same_stream_name`) but doesn't affect the score yet — see limitations.
Baseline (`baseline_service.py`): the most common (mode) historical
value per indicator, from historical reports at that location — meaning
reports older than the current related-report time window, so the baseline
can never be built from the very reports currently being scored as
evidence (that would be circular). Needs at least
`BASELINE_MINIMUM_OBSERVATIONS` (default 5) historical reports or
`baseline.available = False` — never treated as "abnormal" by default.
Confidence scoring (`confidence_service.py`) — deterministic, weighted
sum of 6 sub-scores, each normalized to 0.0-1.0:
Component	Weight	What it measures
Corroboration	30%	count of agreeing nearby reports, saturating at `CORROBORATION_SATURATION_COUNT` (4) to avoid rewarding duplicate spam
Recency	15%	how fresh the report + its corroborators are, relative to the time window
Geographic consistency	15%	how tightly corroborating reports cluster around this one
Indicator agreement	15%	fraction (not count) of nearby reports that agree — penalizes noisy/conflicting sets
Image quality	10%	average Gemini-reported image quality of this report + corroborators
Baseline deviation	15%	1.0 only if a baseline exists AND this report deviates from it; 0.0 otherwise (including when no baseline exists)
`confidence_level`: `HIGH` if score >= `CONFIDENCE_HIGH_THRESHOLD` (0.70),
`MODERATE` if >= `CONFIDENCE_MODERATE_THRESHOLD` (0.40), else `LOW`. A
conflict safety cap additionally forces `HIGH` down to `MODERATE`
whenever conflicting reports are at least as numerous as supporting ones,
even if the raw weighted score alone would clear the threshold.
Evidence fusion (`evidence_fusion_service.py`): orchestrates the above,
classifies related reports as `supporting` or `conflicting` based on
whether they agree with the evaluated report's anomaly signal, and returns
`condition_summary` / `evidence_reasons` / `recommended_action` - the last
is always either "Officer verification recommended." or "Continue
monitoring...", never an automatic decision.
Actionability + exposure risk (Sprint 4)
Two new endpoints turn the Sprint 3 evidence-fusion result into something an
officer can actually act on, without ever crossing into medical territory.
The pipeline is strictly one-directional and each stage only reads the
previous stage's output:
```
ENVIRONMENTAL OBSERVATION -> EVIDENCE FUSION -> CONFIDENCE
    -> EXPOSURE-RISK SIGNAL -> OPERATIONAL REVIEW ACTION
```
It never becomes `OBSERVATION -> DIAGNOSIS` or `OBSERVATION -> OUTBREAK PREDICTION` at any point — there is no code path that produces disease
names, outbreak claims, or confirmed-contamination language, and this is
enforced by test (`test_no_medical_language_in_reasons`).
`GET /api/reports/{report_id}/actionability` (`actionability_service.py`)
does NOT recompute confidence — `confidence_service` (Sprint 3) remains the
sole authority for that. It only interprets the existing
`EvidenceFusionResult` (extended this sprint with an `indicator_severity`
field — NONE/LOW/MODERATE/HIGH, from `indicator_scales.get_indicator_severity`)
into one of three action levels, first-matching-rule wins:
`confidence_level == LOW` or `indicator_severity == NONE` -> `CONTINUE_MONITORING`
`confidence_level == HIGH` AND conflicting < supporting AND
(`indicator_severity == HIGH` OR `supporting >= PRIORITY_REVIEW_MIN_SUPPORTING_COUNT` (3))
-> `PRIORITY_REVIEW`
otherwise -> `REVIEW_RECOMMENDED`
Same principle as Sprint 3's conflict cap: a report can only reach
`PRIORITY_REVIEW` when supporting evidence clearly outweighs conflicting
evidence, never by simple majority.
The exposure-risk signal (`exposure_risk_service.py`) answers a
deliberately narrow question: does this observation, combined with how much
corroborated evidence supports it, look worth flagging for environmental/
public-health review if people might interact with the water? It says
nothing about who is exposed or what illness could result. Deterministic
lookup table (`indicator_severity` x `confidence_level`), then a one-level
bump (capped at ELEVATED) if the location's baseline is available and
deviates:
	LOW conf	MODERATE conf	HIGH conf
NONE	LOW	LOW	LOW
LOW	LOW	LOW	MODERATE
MODERATE	LOW	MODERATE	ELEVATED
HIGH	MODERATE	ELEVATED	ELEVATED
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
FHIR interoperability (Sprint 4)
`GET /api/reports/{report_id}/fhir` (`fhir_service.py`) returns a
FHIR R4-shaped `Observation` resource — not a FHIR server, no validation
against the full spec, no persistence. Isolated in one module so nothing
else in the app is coupled to FHIR structure.
Deliberate choices, all in the "do not fabricate data" spirit:
`subject` references an environmental location, not a Patient
(`{"display": "Stream location (lat, lon) — stream name"}`) — FHIR's base
Observation resource explicitly allows non-Patient subjects, and this is
an environmental observation, not a clinical one. No `reference` id is
invented, only a display string built from real data.
`status` is always `"preliminary"`, never `"final"` — there is no
human/officer verification step yet (that's a later sprint), and FHIR's
own definition of "preliminary" (initial/interim, may be unverified) is
the honest description of AI-extracted, un-reviewed data.
No LOINC/SNOMED codes are invented. Every `code`/`component.code`
uses free-text `CodeableConcept.text` rather than a fabricated coding
system this project hasn't validated against a terminology server.
No patient demographic fields exist anywhere in the resource — there
is nothing to map, so nothing is invented to fill the gap.
Environmental indicators (turbidity, algae, visible waste, color
anomaly, image quality, model confidence) plus evidence-fusion confidence
score/level/related-report-count are represented as `component` entries;
`note` carries the human-readable `condition_summary`.
Environment variables
Backend (`backend/.env`):
Variable	Purpose	Default
`DATABASE_URL`	Postgres connection string	`postgresql+psycopg2://postgres:postgres@localhost:5432/aqua_sentinel`
`CORS_ORIGINS`	Comma-separated allowed frontend origins	`http://localhost:3000`
`UPLOAD_DIR`	Local folder for uploaded images	`uploads`
`MAX_UPLOAD_SIZE_MB`	Max image size	`8`
`GEMINI_API_KEY`	Gemini API key for vision analysis	(required for analysis to run — get one at https://aistudio.google.com/apikey)
`GEMINI_MODEL`	Gemini model to call	`gemini-3.5-flash`
`RELATED_REPORT_RADIUS_METERS`	Related-report geographic radius	`300.0`
`RELATED_REPORT_TIME_WINDOW_MINUTES`	Related-report time window	`120`
`BASELINE_MINIMUM_OBSERVATIONS`	Min. historical reports needed for a baseline	`5`
`CORROBORATION_SATURATION_COUNT`	Supporting-report count where corroboration score maxes out	`4`
`CONFIDENCE_HIGH_THRESHOLD`	Score cutoff for HIGH confidence	`0.70`
`CONFIDENCE_MODERATE_THRESHOLD`	Score cutoff for MODERATE confidence	`0.40`
`PRIORITY_REVIEW_MIN_SUPPORTING_COUNT`	Min. supporting reports (as an OR-alternative to HIGH severity) for `PRIORITY_REVIEW`	`3`
Frontend (`frontend/.env.local`):
Variable	Purpose	Default
`NEXT_PUBLIC_API_BASE_URL`	Backend API base URL	`http://localhost:8000/api`
Known limitations (Sprint 1 + 2 + 3 + 4)
No location dedup — every report creates a new `Location` row, even at
identical coordinates. Related-report/baseline queries compensate for
this via radius search rather than requiring a shared `location_id`.
No authentication — reports are anonymous (`user_id` is nullable).
Local disk storage only — not suitable for production/multi-instance
deployment.
`create_all()` schema management, not Alembic migrations.
If Gemini analysis fails, the report silently reverts to `SUBMITTED` —
there's no retry endpoint yet.
The Gemini call itself was not tested live in this build environment (no
network egress here) — verified structurally + with a mocked HTTP layer.
Evidence-fusion independence limitation: there's no reporter identity
or source verification, so "corroboration" currently just counts report
rows near each other in space/time — it cannot distinguish five reports
from five different people from five re-submissions by one person.
`corroboration_score` saturates at `CORROBORATION_SATURATION_COUNT` (4)
reports specifically to avoid rewarding duplicate spam with unbounded
score growth, but this is a mitigation, not a real independence check.
Sparse baseline: locations with fewer than `BASELINE_MINIMUM_OBSERVATIONS`
(5) historical analyzed reports get `baseline.available = False`, and the
scoring formula treats that as neutral (contributes 0, not a penalty or
bonus) — but it does mean confidence for newly-monitored locations relies
more heavily on corroboration/recency/geography than baseline deviation.
No verified-authority labels yet: officer verification/dismissal
isn't implemented (that's the next sprint), so there's no ground-truth
feedback loop into the scoring yet.
Simplified environmental interpretation: `is_abnormal()` is a coarse
boolean gate (any indicator elevated → abnormal). It doesn't yet weigh
which indicator is more environmentally significant than another, or
handle partial/ambiguous indicator combinations beyond what's in
`evidence_reasons`.
`stream_name` match is surfaced as informational metadata
(`same_stream_name` on related reports) but does not yet affect the
score — left as a documented decision rather than an ad-hoc bonus term
bolted onto the weighted formula.
Actionability/exposure-risk are interpretive layers on top of
Sprint 3's confidence score, not new data sources — a bad confidence
score still produces a bad action recommendation. They add no new
corroboration signal of their own.
FHIR representation is a one-way, in-memory mapping, not FHIR
storage/exchange — nothing is persisted as FHIR, there's no FHIR
server, no terminology validation, and no round-trip (importing a FHIR
resource back into this system isn't supported). It's meant to show what
interoperability could look like, not to be a compliant FHIR endpoint.
`status: "preliminary"` never changes — since there's no officer
verification step yet (Sprint 5), every FHIR resource this system
produces will say "preliminary" regardless of how strong the evidence
is. That's intentional honesty, not a bug, but it does mean the FHIR
output alone can't currently signal "this was reviewed and confirmed."
Next sprint recommendation
Sprint 5: officer review + verified feedback loop. Add an
`officer_service` for verify/dismiss/request-more-evidence actions on a
report (or ideally a persisted `Case` grouping related reports — the spec
in Sprint 3/4 has been operating without one). Once a report is officer-
verified, flip its FHIR `status` to `"final"` and start feeding
verified/dismissed outcomes back as a signal that could eventually
strengthen `confidence_service` — the ground-truth feedback loop noted as
missing in every sprint's limitations section so far.