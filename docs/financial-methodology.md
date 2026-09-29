# Financial Methodology

All calculations are deterministic Python in `backend/app/financial/engine.py`; the language model is never asked to calculate, route, or invent scheme parameters.

## Formulae

1. `project cost = available margin × 10`
2. Route project cost to Micro Finance when it is at or below ₹1,40,000; otherwise route to Term Loan up to ₹50,00,000.
3. `eligible loan = smaller of (project cost × 90%) and scheme maximum loan`.

## Moratorium and repayment assumption

The supplied brief gives a moratorium length but does not specify its interest treatment. For transparent prototype planning, this app assumes payments are paused while monthly interest capitalizes. It then computes a reducing-balance monthly EMI across the stated tenure, rounding at each month, and groups three payments into each displayed quarter. It is not an official lender schedule.
