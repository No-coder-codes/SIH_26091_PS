# Gram Udyog V0.2

**AI-Powered Financial Intelligence for Rural Enterprise** — a polished prototype for Smart India Hackathon problem statement 26091, *AI-Driven Hyper-Local Business Advisory and Financial Structuring Assistant for Rural Micro-Entrepreneurs*.

> **Plan your enterprise before you borrow.**

This prototype demonstrates a rural enterprise feasibility and financial structuring component of the proposed SIH solution. It is **not** an official loan eligibility system and does not replace institutional verification, loan approval, local market validation, or professional financial advice.

## What it does

- Takes a Gujarat location, business category, and available margin capital.
- Captures district, taluka, locality and a business idea for a stronger, explainable assessment record.
- Produces local-demand, competition and business-economics cards labelled as prototype simulation using illustrative/public-data proxies.
- Runs transparent Conservative, Expected and Stress scenarios with deterministic assumptions.
- Deterministically calculates illustrative project capacity, scheme route, eligible loan, and repayment schedule.
- Applies the stated financing percentage and maximum-loan caps.
- Clearly separates the stated moratorium from the repayment period.
- Presents a responsive printable financial blueprint and quarterly schedule.
- Offers an optional OpenAI-powered advisor that explains backend-calculated results only, plus a clearly-labelled deterministic Demo Advisor fallback when no API key is configured.
- Creates a printable Business Decision Brief with validation checklist and assumptions.
- Keeps core calculations available in the browser if the backend or AI is unavailable.

Supported prototype context categories: Dairy, Textile, Agriculture. Their cost/revenue components, feasibility signals, economics and scenarios are illustrative planning metadata, not official government data or verified local statistics. The prototype has no live OSM, AGMARKNET, Census, PostGIS, RAG, Bhashini, government API, or institutional integration.

## Financial methodology

The supplied problem-statement parameters are implemented in `backend/app/financial/engine.py`.

| Scheme | Project cost | Financing | Maximum loan | Interest | Tenure | Moratorium |
|---|---:|---:|---:|---:|---:|---:|
| Micro Finance | Up to ₹1,40,000 | Up to 90% | ₹1,25,000 | 6.5% p.a. | 3 years | 3 months |
| Term Loan | Above ₹1,40,000 to ₹50,00,000 | Up to 90% | ₹45,00,000 | 8% p.a. | 7 years | 6 months |

- `project cost = margin capital × 10` (the supplied 10% contribution rule)
- `eligible loan = min(project cost × 90%, scheme maximum loan)`
- Project cost above ₹50,00,000 is intentionally shown as outside the stated scheme range.
- **Repayment assumption:** no payment is made during moratorium; interest compounds monthly into principal. Afterwards, a monthly reducing-balance EMI is calculated for the stated tenure and aggregated into a quarterly display. It is an illustrative planning method, not an official lender amortization schedule.

### Note on the supplied ₹20,000 edge example

The brief’s edge example labels a ₹2,00,000 project as Micro Finance, but its explicit routing rules send every project above ₹1,40,000 to **Term Loan**. This build honors the explicit routing rules. The Micro cap can be demonstrated at a ₹14,000 margin (₹1,40,000 project × 90% = ₹1,26,000, capped at ₹1,25,000).

## Architecture

```text
frontend/                 Responsive dependency-free web UI + offline calculation fallback
backend/app/financial/    Pure Python deterministic engine
backend/app/data/         Structured business-category metadata
backend/app/services/     Deterministic feasibility/scenario layer and grounded advisor fallback
backend/app/main.py       FastAPI endpoints and optional OpenAI adapter
backend/tests/            Engine unit tests
```

The compact static frontend was chosen over Vite/React because the supplied environment has Node but no npm; it avoids a build dependency while preserving the intended browser experience. The backend remains FastAPI + pure Python as requested.

## Run locally

Requires Python 3.10+.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
$env:PYTHONPATH = "$PWD\backend"
uvicorn app.main:app --reload --app-dir backend
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). The frontend is served by FastAPI, so no separate frontend command is required.

## OpenAI configuration

Copy `.env.example` to `.env` and provide `OPENAI_API_KEY`. Load it using your local environment tooling before starting the backend. The key is read on the backend only; it is never sent to browser code. Without a key, the app explicitly states that the AI Advisor is unavailable while calculations continue.

## API

- `POST /api/financial/calculate`
- `POST /api/ai/chat`
- `GET /api/schemes`
- `GET /api/business-categories`

Example input:

```json
{"location":"Vadodara, Gujarat","business_category":"dairy","margin_capital":100000}
```

## Tests

```powershell
$env:PYTHONPATH = "$PWD\backend"
py -m unittest discover -s backend\tests -v
```

Covered: demo calculation, Micro Finance route, Term Loan route, maximum Micro loan cap (at its mathematically valid threshold), outside-range behavior, invalid capital, moratorium handling, schedule generation, feasibility/scenario calculations, API validation, and the Demo Advisor fallback.

## Demo flow

Click **Load demo**. It loads fictional entrepreneur Ramesh Patel’s scenario: Sevasi, Vadodara; Dairy; ₹1,00,000 margin → ₹10,00,000 project capacity → ₹9,00,000 indicative financing → Term Loan Scheme → 8% → 7 years → 6-month moratorium. It then fills feasibility, business economics, scenarios, repayment, decision trail, printable brief, and the grounded Demo Advisor.

For a maximum-loan-cap demonstration use ₹14,000 margin. For a straightforward Micro Finance scenario use ₹10,000 margin.

## Limits and future direction

No live market data, loan application, banking connection, credit scoring, official local statistics, authentication, or business-success prediction is implemented. The structure leaves room for scale architecture such as future hyper-local market intelligence, competitor mapping, demand/price estimates, and a risk engine.
