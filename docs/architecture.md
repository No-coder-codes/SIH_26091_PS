# Architecture

Gram Udyog uses a deterministic core behind a thin HTTP API. `financial/engine.py` contains all scheme routing, loan-cap, moratorium, and repayment calculations. `main.py` validates inputs and forwards structured output to the optional OpenAI explanation adapter. It never permits the model to calculate financial values.

The browser UI uses the same transparent calculation model only as an offline fallback. When the FastAPI service is present, the server result is authoritative. Business context is loaded from structured JSON on the backend and mirrored in the UI for offline presentation.

Future modules should add data adapters behind APIs rather than coupling market data, risk logic, or AI to the financial engine.
