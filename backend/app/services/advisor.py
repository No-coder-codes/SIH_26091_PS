"""Grounded Advisor: an optional OpenAI explainer with deterministic demo fallback.

Supports robust intent classification across English and Hinglish with multiple
grounded response variants for each financial intent.
"""
from __future__ import annotations

import os


def classify_intent(message: str) -> str:
    """Classify user query into one of 9 supported intents or 'unknown'."""
    q = message.lower().strip()

    # 1. Scheme selection
    if any(k in q for k in ["scheme", "route", "kyu mili", "why term loan", "why micro", "why this", "which scheme", "select"]):
        return "scheme"

    # 2. Financing calculation
    if any(k in q for k in ["financ", "calculat", "how much loan", "loan amount", "9 lakh", "contribution", "margin", "kaise calculate", "kitna loan"]):
        return "financing"

    # 3. Repayment / EMI
    if any(k in q for k in ["repay", "emi", "schedule", "instalment", "installment", "monthly payment", "bharna", "kaise chukaye", "how will i repay"]):
        return "repayment"

    # 4. Moratorium
    if any(k in q for k in ["moratorium", "immediately", "grace", "pause"]):
        return "moratorium"

    # 5. Risk
    if any(k in q for k in ["risk", "wrong", "careful", "khatra", "danger", "problem"]):
        return "risk"

    # 6. Scenario analysis
    if any(k in q for k in ["scenario", "stress", "conservative", "expected", "revenue fall", "revenue drop", "revenue kam"]):
        return "scenario"

    # 7. Working Capital
    if any(k in q for k in ["working capital", "wc"]):
        return "working_capital"

    # 8. Assumptions / Data sources
    if any(k in q for k in ["assumption", "government", "real data", "official", "census", "agmarknet", "where does this data"]):
        return "assumptions"

    # 9. General result summary
    if any(k in q for k in ["summar", "overview", "blueprint", "key number", "sab batao", "explain my result"]):
        return "summary"

    return "unknown"


def demo_advisor_reply(message: str, context: dict) -> str:
    """Answer user questions with intent classification and multiple grounded response variants."""
    intent = classify_intent(message)
    variant_idx = abs(hash(message.strip().lower()))

    # Extract authoritative backend context
    scheme = context.get("scheme", "the stated scheme route")
    project = float(context.get("project_cost") or 0)
    loan = float(context.get("loan_amount") or 0)
    margin = float(context.get("margin_capital") or 0)
    moratorium = context.get("moratorium_months") or 6
    tenure = context.get("tenure_years") or 7
    rate = float(context.get("interest_rate") or 0.08) * 100
    quarterly = float(context.get("quarterly_payment") or 0)
    total_repayment = float(context.get("total_repayment") or 0)

    scenarios = context.get("analysis", {}).get("scenarios", [])
    stress = next((item for item in scenarios if item["name"] == "Stress"), {})
    conservative = next((item for item in scenarios if item["name"] == "Conservative"), {})
    expected = next((item for item in scenarios if item["name"] == "Expected"), {})

    stress_cash = float(stress.get("cash_available_for_debt_service") or 0)
    stress_debt = float(stress.get("monthly_debt_service") or 0)
    stress_stress = stress.get("debt_stress", "Under pressure")
    stress_coverage = float(stress.get("debt_coverage_ratio") or 0)

    cons_cash = float(conservative.get("cash_available_for_debt_service") or 0)
    exp_cash = float(expected.get("cash_available_for_debt_service") or 0)
    exp_coverage = float(expected.get("debt_coverage_ratio") or 0)

    wc = float(context.get("analysis", {}).get("business_economics", {}).get("working_capital_requirement") or 0)

    if intent == "scheme":
        variants = [
            f"Based on your ₹{margin:,.0f} margin capital, the 10% contribution rule calculates an indicative project capacity of ₹{project:,.0f}. Under the configured SIH problem thresholds (Micro ≤ ₹1.4L; Term Loan ≤ ₹50L), a project of ₹{project:,.0f} is routed to the {scheme}.",
            f"The scheme follows from the calculated project size (₹{project:,.0f}) derived from your ₹{margin:,.0f} margin contribution. Project cost above ₹1,40,000 routes to the {scheme} with 90% indicative financing up to ₹45,00,000.",
            f"Your ₹{margin:,.0f} margin supports ₹{project:,.0f} total project capacity under the 10% contribution formula. The deterministic rule engine routes this capacity to the {scheme}."
        ]
        return variants[variant_idx % len(variants)]

    if intent == "financing":
        variants = [
            f"Indicative financing is calculated as 90% of your project capacity (₹{project:,.0f}), subject to scheme caps. For your ₹{margin:,.0f} margin, 10x capacity yields ₹{project:,.0f}, giving ₹{loan:,.0f} in indicative financing.",
            f"Your ₹{margin:,.0f} margin capital establishes ₹{project:,.0f} project capacity under the 10% contribution rule. 90% of this capacity equals ₹{loan:,.0f} indicative financing under the {scheme}.",
            f"The financial engine applies a 10% own-contribution rule to determine ₹{project:,.0f} project size. 90% of this capacity gives ₹{loan:,.0f} indicative financing (capped at scheme maximums)."
        ]
        return variants[variant_idx % len(variants)]

    if intent == "repayment":
        variants = [
            f"Repayment for the {scheme} spans {tenure} years at {rate:.1f}% annual interest after a {moratorium}-month moratorium. Three monthly instalments aggregate to a ₹{quarterly:,.0f} quarterly payment display (Total repayment: ₹{total_repayment:,.0f}).",
            f"After a {moratorium}-month moratorium (during which interest capitalizes), regular reducing-balance EMI payments occur over {tenure} years, grouped into ₹{quarterly:,.0f} per displayed quarter.",
            f"The repayment model calculates monthly reducing-balance EMIs over {tenure} years at {rate:.1f}% p.a. starting after {moratorium} months, with ₹{quarterly:,.0f} due per displayed quarter."
        ]
        return variants[variant_idx % len(variants)]

    if intent == "moratorium":
        variants = [
            f"The prototype applies a {moratorium}-month moratorium assumption during which no scheduled repayments are required. Monthly interest capitalizes into principal before regular repayments begin.",
            f"During the {moratorium}-month moratorium, repayment is paused while monthly interest compounds into principal. Repayment starts in month {int(moratorium) + 1} over a {tenure}-year tenure.",
            f"Repayment does not start immediately; payments pause for {moratorium} months with interest capitalization. This is a disclosed prototype planning assumption, not an official lender schedule."
        ]
        return variants[variant_idx % len(variants)]

    if intent == "risk":
        variants = [
            f"Key risks include revenue fluctuation, input cost shifts, and cash flow timing. Under the Stress scenario (-35% revenue), monthly cash for debt service drops to ₹{stress_cash:,.0f} against ₹{stress_debt:,.0f} due, marked '{stress_stress}'.",
            f"Primary enterprise risks involve buyer demand swings and supplier credit terms. If monthly revenue drops 35% in the Stress test, debt coverage falls to {stress_coverage:.2f}x. Ensure sufficient cash reserves.",
            f"The main risk is fixed debt service during revenue slowdowns. In the Stress test, available cash for debt drops to ₹{stress_cash:,.0f}/month against ₹{stress_debt:,.0f} due. Validate buyers and working capital reserves."
        ]
        return variants[variant_idx % len(variants)]

    if intent == "scenario":
        variants = [
            f"The prototype tests 3 deterministic scenarios: Conservative (-20% revenue: ₹{cons_cash:,.0f}/mo cash), Expected (baseline: ₹{exp_cash:,.0f}/mo cash), and Stress (-35% revenue: ₹{stress_cash:,.0f}/mo cash, coverage {stress_coverage:.2f}x).",
            f"Scenarios evaluate debt service under revenue shocks. Baseline yields {exp_coverage:.2f}x debt coverage; a 35% revenue drop in Stress scenario lowers cash for debt to ₹{stress_cash:,.0f} against ₹{stress_debt:,.0f} monthly debt service.",
            f"In the Stress scenario (35% revenue reduction), available debt service cash drops from ₹{exp_cash:,.0f} to ₹{stress_cash:,.0f}/month, helping evaluate business resilience."
        ]
        return variants[variant_idx % len(variants)]

    if intent == "working_capital":
        variants = [
            f"Working capital is the operating cash needed for inventory, inputs, and daily operations before sales receipts arrive. For this sector profile, the prototype assumption indicates ₹{wc:,.0f}.",
            f"The category profile estimates an illustrative working capital requirement of ₹{wc:,.0f}. Verify actual credit terms and inventory lead times with local suppliers.",
            f"Your blueprint shows an illustrative working capital requirement of ₹{wc:,.0f}. This represents the liquid buffer required to maintain continuous operations during local payment cycles."
        ]
        return variants[variant_idx % len(variants)]

    if intent == "assumptions":
        variants = [
            f"This blueprint combines stated SIH problem-statement rules (10% margin, scheme limits) with illustrative category assumptions (turnover, operating cost, working capital). No live government or market dataset is connected.",
            f"All calculations rely on deterministic problem parameters and prototype business proxies. The prototype does not query live AGMARKNET, Census, GIS, or bank eligibility databases.",
            f"Figures are derived from explicit problem-statement financial formulas and sector ratio proxies. Institutional loan sanction, local market prices, and buyer demand require independent verification."
        ]
        return variants[variant_idx % len(variants)]

    if intent == "summary":
        variants = [
            f"Blueprint summary: ₹{margin:,.0f} margin capital → ₹{project:,.0f} project capacity → ₹{loan:,.0f} indicative financing via {scheme} ({rate:.1f}%, {tenure} yrs, {moratorium}-mo moratorium, ₹{quarterly:,.0f}/quarter payment).",
            f"Key calculated numbers: ₹{project:,.0f} indicative project cost, ₹{loan:,.0f} indicative financing on {scheme}, with ₹{quarterly:,.0f} quarterly repayment after a {moratorium}-month moratorium.",
            f"Summary: {scheme} route with ₹{project:,.0f} capacity, ₹{loan:,.0f} indicative loan at {rate:.1f}% p.a. Expected debt coverage is {exp_coverage:.2f}x, dropping to {stress_coverage:.2f}x under Stress test."
        ]
        return variants[variant_idx % len(variants)]

    # Unsupported intent fallback
    fallbacks = [
        "I can explain the calculated financing, scheme route, repayment model, scenarios, risks and assumptions in this blueprint. I don't have verified data for that specific question.",
        "This advisor explains calculated blueprint numbers only. I don't have verified data for questions outside the available financial context."
    ]
    return fallbacks[variant_idx % len(fallbacks)]


def advisor_mode() -> str:
    return "live" if os.getenv("OPENAI_API_KEY") else "demo"
