# HydroLens 
 
**AI-powered environmental intelligence for citizen-reported water observations.** 
 
HydroLens is a personal AI/ML project that analyzes geo-tagged water-body photographs and converts them into structured, explainable environmental observations. 
 
The system combines AI vision, nearby and recent observations, historical context, deterministic confidence scoring, actionability, exposure-risk signaling, and human verification into a single traceable workflow. 
 
> **Important:** HydroLens analyzes visible conditions in photographs. It does not perform laboratory water-quality testing, provide medical diagnoses, determine regulatory violations, or predict disease outbreaks. 
 
--- 
 
## Overview 
 
A citizen submits a photograph of a local stream, river, lake, or other water body together with location information. 
 
HydroLens then: 
 
1. Analyzes the image using Gemini vision. 
2. Extracts observable environmental indicators. 
3. Finds nearby and recent reports that may support or conflict with the observation. 
4. Compares the observation with the location's historical baseline when sufficient history exists. 
5. Calculates a deterministic and explainable confidence score. 
6. Generates an operational review recommendation and exposure-risk signal. 
7. Allows an authorized reviewer to verify or reject the observation. 
8. Preserves verification history and evidence provenance. 
9. Exposes the result through a FHIR-compatible `Observation` representation. 
10. Presents the information through a monitoring dashboard and case-management interface. 
 
The objective is not to replace human judgment, but to make citizen observations more structured, explainable, and useful for environmental review. 
 
--- 
 
## Problem 
 
Citizen-generated environmental observations can provide useful local information, but individual photographs are inherently noisy. 
 
A single image may be: 
 
- low quality 
- affected by lighting or weather 
- captured at an unusual moment 
- difficult to interpret visually 
- incorrectly interpreted by an AI model 
 
Treating a single AI-generated observation as ground truth is therefore inappropriate. 
 
At the same time, ignoring citizen reports because they are imperfect can discard potentially useful environmental signals. 
 
HydroLens addresses this by combining multiple sources of evidence rather than relying on a single photograph. 
 
--- 
 
## Solution 
 
HydroLens follows a simple principle: 
 
> **Do not ask only what one photograph shows. Ask what the available evidence supports when observations are considered together.** 
 
Corroboration, disagreement, geographic proximity, recency, image quality, and historical context contribute to a deterministic confidence score. 
 
Human verification remains a separate stage and is never replaced by AI confidence. 
 
--- 
 
## Core Workflow 
 
```text 
Citizen submits photo + location 
            | 
            v 
      Gemini Vision 
            | 
            v 
   Environmental Observation 
  - Algae 
  - Turbidity 
  - Visible Waste 
  - Color Anomaly 
  - Image Quality 
            | 
            v 
       Evidence Fusion 
  - Nearby reports 
  - Recent reports 
  - Historical baseline 
            | 
            v 
    Deterministic Confidence 
            | 
            v 
 Actionability + Exposure Risk 
            | 
            v 
      Human Verification 
      VERIFIED / REJECTED 
            | 
            v 
   Audit Trail + Provenance 
            | 
            v 
      FHIR Observation 
            | 
            v 
 Dashboard + Case Management only this much??


## Key Features

### AI-Powered Image Analysis

HydroLens uses Google Gemini vision to analyze citizen-submitted water-body photographs and extract observable environmental indicators:

- Turbidity
- Algae
- Visible waste
- Color anomalies
- Image quality
- AI model confidence

The AI layer is limited to visual observation. It does not generate medical diagnoses, confirmed contamination claims, or disease/outbreak predictions.

AI responses are schema-validated before being persisted, preventing invalid or malformed model output from entering the database.

---

### Evidence Fusion

A single image may not provide enough evidence to understand an environmental condition.

HydroLens therefore combines:

- Nearby and recent analyzed reports
- Supporting and conflicting observations
- Geographic consistency
- Temporal recency
- Indicator agreement
- Image quality
- Historical baseline deviation

The result is a deterministic and explainable confidence score rather than a black-box decision.

### Confidence Model

| Component | Weight | Purpose |
|---|---:|---|
| Corroboration | 30% | Agreement from nearby reports |
| Recency | 15% | Freshness of observations |
| Geographic consistency | 15% | Spatial relationship between reports |
| Indicator agreement | 15% | Agreement between observed conditions |
| Image quality | 10% | Quality of visual evidence |
| Baseline deviation | 15% | Difference from historical local conditions |

Confidence levels are derived from configured thresholds:

```text
HIGH       >= 0.70
MODERATE   >= 0.40
LOW        < 0.40
````

A conflict-safety rule also prevents strong conflicting evidence from being ignored simply because the raw weighted score is high.

---

## Historical Baseline

HydroLens can compare new observations with the historical conditions of a location.

A baseline is created only when enough historical observations are available.

```text
Default minimum historical observations: 5
```

The current nearby/recent reports are excluded from baseline construction so that the same observations are not used both as evidence and as historical baseline data.

When there is insufficient history, the system does not automatically assume that a location is abnormal.

---

## Actionability & Exposure Risk

The evidence-fusion result is translated into an operational review recommendation.

Possible action levels:

```text
CONTINUE_MONITORING
REVIEW_RECOMMENDED
PRIORITY_REVIEW
```

The actionability layer does not recalculate confidence. It interprets the existing evidence-fusion result.

HydroLens also produces a narrow environmental exposure-risk signal based on indicator severity, confidence, and available baseline evidence.

It does **not** attempt to determine:

* Who is exposed
* What illness may result
* Medical diagnosis
* Infection probability
* Disease or outbreak probability

---

## Human Verification & Trust

A core principle of HydroLens is:

> **AI-generated observations are not automatically ground truth.**

The system keeps AI analysis and human verification separate.

| Concept             | Meaning                                               |
| ------------------- | ----------------------------------------------------- |
| AI Analysis Status  | Whether the image has completed AI analysis           |
| Verification Status | Whether a human reviewer has reviewed the observation |

Typical lifecycle:

```text
SUBMITTED
    ↓
ANALYZING
    ↓
ANALYZED
    ↓
UNVERIFIED
    ↓
VERIFIED / REJECTED
```

Only an authorized reviewer can perform the verification step.

Every verification action creates an audit event containing the previous status, new status, reviewer reference, note, and timestamp.

The original AI observation remains separate from the human verification record.

---

## Authentication & Roles

HydroLens includes role-based authentication.

### Citizen

Citizens can:

* Create an account
* Log in securely
* Submit water observations
* Access their permitted reports

### Reviewer

Reviewers represent the environmental-review workflow and can access protected monitoring, case-management, and verification functionality.

Authentication uses token-based authorization.

Sensitive credentials such as the Gemini API key remain server-side and are never exposed to the frontend.

---

## Dashboard & Case Management

HydroLens provides a monitoring dashboard and case-management interface for reviewing analyzed observations.

### Dashboard

```text
GET /api/dashboard/summary
```

Provides live information such as:

* Total reports
* Analyzed reports
* Pending analysis
* Confidence levels
* Verification status
* Reports requiring review

### Cases

```text
GET /api/cases
GET /api/cases/{id}
```

Case views can include:

* Environmental signal summary
* Confidence score and level
* Exposure-risk level
* Action level
* Supporting evidence
* Conflicting evidence
* Evidence provenance
* Historical baseline
* Verification history
* FHIR representation

---

## FHIR Interoperability

HydroLens exposes a FHIR R4-shaped `Observation` representation:

```text
GET /api/reports/{report_id}/fhir
```

The resource can contain:

* Environmental indicators
* Image quality
* AI model confidence score
* Evidence-fusion confidence
* Confidence level
* Related-report count
* Verification status

The implementation deliberately avoids inventing patient information or unvalidated clinical terminology.

This is an interoperability representation, not a complete FHIR server.

---

## Architecture

```text
project-root/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── core/
│   ├── alembic/
│   ├── evaluation/
│   ├── tests/
│   └── Dockerfile
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── Dockerfile
│
├── scripts/
├── docker-compose.yml
└── README.md
```

The backend follows a modular architecture with separate services for vision analysis, evidence fusion, confidence, actionability, exposure risk, verification, FHIR, dashboard aggregation, and storage.

This keeps individual responsibilities isolated and makes the system easier to test and extend.

---

## Technology Stack

| Layer            | Technologies                                      |
| ---------------- | ------------------------------------------------- |
| Backend          | Python, FastAPI, SQLAlchemy, Pydantic             |
| Database         | PostgreSQL                                        |
| Migrations       | Alembic                                           |
| AI               | Google Gemini Vision                              |
| Frontend         | Next.js, React, TypeScript, Tailwind CSS          |
| Interoperability | FHIR R4-shaped Observation                        |
| Testing          | pytest, SQLite test database, mocked AI responses |

---

## API Highlights

| Endpoint                              | Purpose                    |
| ------------------------------------- | -------------------------- |
| `POST /api/auth/signup`               | Citizen registration       |
| `POST /api/auth/login`                | User authentication        |
| `GET /api/auth/me`                    | Current authenticated user |
| `POST /api/reports`                   | Submit a water observation |
| `GET /api/reports/{id}/evidence`      | Evidence-fusion analysis   |
| `GET /api/reports/{id}/actionability` | Actionability result       |
| `GET /api/reports/{id}/fhir`          | FHIR Observation           |
| `GET /api/reports/{id}/verification`  | Verification history       |
| `POST /api/reports/{id}/verify`       | Reviewer verification      |
| `GET /api/dashboard/summary`          | Dashboard summary          |
| `GET /api/cases`                      | Case list                  |
| `GET /api/cases/{id}`                 | Case details               |

---

## Local Setup

### Backend

```bash
cd backend

python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create:

```text
backend/.env
```

using:

```text
backend/.env.example
```

Configure at minimum:

```text
DATABASE_URL
GEMINI_API_KEY
JWT_SECRET_KEY
```

Run migrations:

```bash
alembic upgrade head
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

Development API documentation:

```text
http://127.0.0.1:8000/docs
```

---

### Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:3000
```

Configure:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
```

---

## Testing

### Backend

```bash
cd backend
pytest -q
```

### Frontend

```bash
cd frontend
npm run build
```

Automated backend tests use mocked Gemini responses, so the test suite does not require live AI API calls.

---

## Evaluation

HydroLens includes internal evaluation scenarios for checking deterministic application behavior.

The evaluation focuses on:

* AI observation handling
* Schema validation
* Evidence-fusion logic
* Confidence scoring
* Conflicting evidence
* Actionability
* Verification behavior
* Deterministic outputs

These evaluations are intentionally small and are **not scientific benchmarks** or statistically representative accuracy measurements.

---

## Security

Sensitive credentials must never be committed to source control.

Do not commit:

```text
.env
.env.local
.venv/
venv/
node_modules/
test-images/
```

The Gemini API key is server-side only.

Testing images are kept separately from the application source and are not required for the application to run.

---

## Deployment

HydroLens can be deployed using separate frontend, backend, database, and AI services.

```text
                 ┌─────────────────────┐
                 │       Vercel        │
                 │   Next.js Frontend  │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │       Render        │
                 │   FastAPI Backend   │
                 └────────┬─────┬──────┘
                          │     │
                 ┌────────┘     └─────────┐
                 ▼                        ▼
          ┌───────────────┐        ┌───────────────┐
          │      Neon     │        │    Gemini     │
          │   PostgreSQL  │        │      API      │
          └───────────────┘        └───────────────┘
```

For production-scale deployment, uploaded images should use persistent object storage rather than local filesystem storage.

---

## Limitations

HydroLens has several deliberate limitations:

* Visual indicators are not laboratory measurements.
* AI observations can be incorrect.
* AI model confidence is a model-reported score, not a scientifically calibrated probability.
* Related-report detection cannot independently establish whether reports come from independent observers.
* Historical baselines require sufficient historical data.
* Human verification improves traceability but does not establish scientific certainty.
* FHIR output is a FHIR-shaped representation rather than a complete FHIR server.
* Evidence and dashboard calculations are currently designed for personal-project scale.
* Local image storage is suitable for development but should be replaced with persistent object storage for larger deployments.
* Internal evaluation data is limited and is not statistically representative.

---

## Future Improvements

* Persistent object storage for uploaded images
* Larger real-world evaluation datasets
* More rigorous environmental validation
* Interactive geographic mapping
* Cached or precomputed evidence and confidence results
* Stronger duplicate and spam detection
* Verified-outcome feedback loops
* Expanded environmental indicators
* More complete FHIR interoperability
* Production-grade monitoring and observability
* Scalable deployment architecture

---

## Project Philosophy

HydroLens is built around a simple principle:

> **AI should help organize evidence, not manufacture certainty.**

The system therefore separates:

```text
AI Observation
      ↓
Evidence
      ↓
Confidence
      ↓
Actionability
      ↓
Human Verification
```

Every stage is designed to remain modular, explainable, testable, and traceable.

---

## Disclaimer

HydroLens is a personal software and AI/ML engineering project for environmental observation and workflow experimentation.

It does not provide certified water-quality measurements, medical advice, regulatory determinations, contamination certification, or disease/outbreak prediction.


