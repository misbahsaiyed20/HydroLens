# Aqua Sentinel

A standalone AI/ML environmental intelligence project: citizens submit
geo-tagged stream photos, AI vision extracts observable environmental
indicators, evidence fusion combines and cross-checks observations, and a
human verification layer keeps AI output from being treated as ground
truth. The system does **not** diagnose disease or predict outbreaks — it
turns citizen observations into explainable, human-reviewable evidence
(observable environmental indicators, exposure-risk signals, evidence
confidence) that a person can verify or reject. This repo implements
**Sprints 1–5**: database foundation + report submission, AI vision
analysis, evidence fusion, actionability + FHIR-compatible interoperability,
and now human verification + auditability.

## Implemented scope (Sprints 1–5)

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
- `GET /api/reports/{report_id}/actionability` — deterministic operational
  recommendation (CONTINUE_MONITORING / REVIEW_RECOMMENDED /
  PRIORITY_REVIEW) plus an exposure-risk signal (LOW / MODERATE /
  ELEVATED), derived from the evidence-fusion result. See "Actionability +
  exposure risk (Sprint 4)" below.
- `GET /api/reports/{report_id}/fhir` — FHIR-compatible Observation
  resource for the report, for future interoperability. See "FHIR
  interoperability (Sprint 4)" below.
- `POST /api/reports/{report_id}/verify` — records a human verification
  decision (VERIFIED or REJECTED) on an already-analyzed report, without
  ever touching the AI-generated `Observation`. See "Trust architecture
  (Sprint 5)" below.
- `GET /api/reports/{report_id}/verification` — current verification state
  + full audit history for a report.

Explicitly **not** built yet: case creation grouping multiple reports,
real authentication (verifier identity is a free-text reference, not a
login), Alembic migrations, a retry endpoint for failed AI analyses.

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
| `RELATED_REPORT_RADIUS_METERS` | Related-report geographic radius | `300.0` |
| `RELATED_REPORT_TIME_WINDOW_MINUTES` | Related-report time window | `120` |
| `BASELINE_MINIMUM_OBSERVATIONS` | Min. historical reports needed for a baseline | `5` |
| `CORROBORATION_SATURATION_COUNT` | Supporting-report count where corroboration score maxes out | `4` |
| `CONFIDENCE_HIGH_THRESHOLD` | Score cutoff for HIGH confidence | `0.70` |
| `CONFIDENCE_MODERATE_THRESHOLD` | Score cutoff for MODERATE confidence | `0.40` |
| `PRIORITY_REVIEW_MIN_SUPPORTING_COUNT` | Min. supporting reports (as an OR-alternative to HIGH severity) for `PRIORITY_REVIEW` | `3` |

**Frontend** (`frontend/.env.local`):
| Variable | Purpose | Default |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Backend API base URL | `http://localhost:8000/api` |

## Known limitations (Sprint 1 + 2 + 3 + 4 + 5)

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
- **No verified-authority labels feeding back into scoring**: verification
  now exists (Sprint 5) but is deliberately kept out of
  `confidence_service`'s formula — see "Evidence provenance" above for why.
  There's still no feedback loop where verified/rejected outcomes adjust
  future scoring; that would be a real, separately-justified design choice
  for a later sprint.
- **`status: "preliminary"` now changes** (superseding the Sprint 4 note
  below) — UNVERIFIED stays `preliminary`, but VERIFIED → `final` and
  REJECTED → `cancelled` as of Sprint 5. See "FHIR implications" above.
- **Simplified environmental interpretation**: `is_abnormal()` is a coarse
  boolean gate (any indicator elevated → abnormal). It doesn't yet weigh
  which indicator is more environmentally significant than another, or
  handle partial/ambiguous indicator combinations beyond what's in
  `evidence_reasons`.
- `stream_name` match is surfaced as informational metadata
  (`same_stream_name` on related reports) but does not yet affect the
  score — left as a documented decision rather than an ad-hoc bonus term
  bolted onto the weighted formula.
- **Actionability/exposure-risk are interpretive layers on top of
  Sprint 3's confidence score, not new data sources** — a bad confidence
  score still produces a bad action recommendation. They add no new
  corroboration signal of their own.
- **FHIR representation is a one-way, in-memory mapping, not FHIR
  storage/exchange** — nothing is persisted as FHIR, there's no FHIR
  server, no terminology validation, and no round-trip (importing a FHIR
  resource back into this system isn't supported). It's meant to show what
  interoperability could look like, not to be a compliant FHIR endpoint.
- **`verifier_reference` is an unauthenticated free-text string** — there
  is no login/auth system, so anyone who can reach the API can "verify" a
  report as anyone. It's stored (for the audit trail) but never exposed in
  FHIR output. This is a real security gap for anything beyond a personal
  project — see "Architecture should allow authentication to be added
  properly later" intent in `verification_service.py`.
- **Enum naming collision (pre-existing, not fixed this sprint)**:
  `ReportStatus` (Sprint 1) already had unused `VERIFIED`/`DISMISSED`
  values that were never wired to any code path (confirmed: zero
  references anywhere in the codebase). Sprint 5's new `VerificationStatus`
  enum also has a `VERIFIED` value, on a *different* column
  (`verification_status`, not `status`). The two are unrelated, but the
  name overlap is a real readability risk — `report.status` and
  `report.verification_status` could both independently say `"VERIFIED"`
  for unrelated reasons. Left untouched here rather than rewrite an
  existing enum unprompted; worth cleaning up (e.g. removing the dead
  `ReportStatus` values) in a future sprint.
- **No PII scrubbing on `verifier_reference`/`note`** — these are
  free-text fields a caller could put an email or real name into; they're
  stored in the audit trail (needed for auditability) but nothing
  validates or redacts their content.

## Next sprint recommendation

**Sprint 6: real authentication + case grouping.** Two gaps stand out most
now that verification exists: (1) `verifier_reference` is an
unauthenticated free-text string — add real login/auth so verification
actions are tied to an actual accountable identity, not a typed-in name;
(2) reports are still scored individually with no persisted `Case`
grouping related/corroborating reports together — a real Case model would
also be the natural place to let verified/rejected outcomes start
influencing future confidence scoring (the "verified feedback loop" noted
as missing since Sprint 3), since that's a decision big enough to deserve
its own sprint rather than being folded into verification's introduction
here.
