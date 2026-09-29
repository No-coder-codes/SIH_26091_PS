"""Deterministic prototype feasibility and scenario layer.

Values use openly displayed business assumptions only. They are not live market,
government, census, OSM, or institutional datasets.
"""
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from app.financial.engine import money

ASSUMPTIONS_PATH = Path(__file__).resolve().parents[1] / "data" / "prototype_assumptions.json"
ASSUMPTIONS = json.loads(ASSUMPTIONS_PATH.read_text(encoding="utf-8"))


def _status(coverage: Decimal) -> str:
    if coverage >= Decimal("1.35"):
        return "More headroom"
    if coverage >= Decimal("1.00"):
        return "Watch closely"
    return "Under pressure"


def analyse_feasibility(category: str, financial: dict, location: str) -> dict:
    """Return transparent illustrative economics and three deterministic scenarios."""
    profile = ASSUMPTIONS[category]
    project_cost = Decimal(str(financial["project_cost"]))
    monthly_repayment = Decimal(str(financial["quarterly_payment"])) / Decimal("3")
    baseline_revenue = money(project_cost * Decimal(str(profile["monthly_turnover_ratio"])))
    operating_cost = money(baseline_revenue * Decimal(str(profile["operating_cost_ratio"])))
    monthly_margin = money(baseline_revenue - operating_cost)
    working_capital = money(baseline_revenue * Decimal(str(profile["working_capital_ratio"])))

    scenario_definitions = [
        ("Conservative", Decimal("0.80"), Decimal("0.98"), "Revenue assumption: 20% below the baseline"),
        ("Expected", Decimal("1.00"), Decimal("1.00"), "Revenue assumption: baseline illustrative case"),
        ("Stress", Decimal("0.65"), Decimal("0.98"), "Revenue assumption: 35% below the baseline"),
    ]
    scenarios = []
    for name, revenue_factor, cost_factor, note in scenario_definitions:
        revenue = money(baseline_revenue * revenue_factor)
        costs = money(operating_cost * cost_factor)
        cash_for_debt = money(revenue - costs)
        coverage = Decimal("0") if monthly_repayment == 0 else money(cash_for_debt / monthly_repayment)
        scenarios.append({
            "name": name,
            "revenue_assumption": float(revenue),
            "operating_cost": float(costs),
            "cash_available_for_debt_service": float(cash_for_debt),
            "monthly_debt_service": float(money(monthly_repayment)),
            "debt_coverage_ratio": float(coverage),
            "debt_stress": _status(coverage),
            "sustainability": "Indicative only — validate local prices and buyers",
            "assumption_note": note,
        })

    return {
        "label": "Prototype simulation using illustrative/public-data proxies",
        "location_context": location,
        "feasibility": {
            "catchment": profile["catchment"],
            "demand_signal": profile["demand_signal"],
            "demand_status": "Promising to validate",
            "enterprise_density": profile["competition_signal"],
            "saturation_indicator": "Illustrative / unverified",
            "opportunity_status": "Validate before committing",
        },
        "business_economics": {
            "estimated_monthly_revenue": float(baseline_revenue),
            "estimated_monthly_operating_cost": float(operating_cost),
            "estimated_monthly_margin": float(monthly_margin),
            "working_capital_requirement": float(working_capital),
            "monthly_debt_service": float(money(monthly_repayment)),
        },
        "scenarios": scenarios,
        "assumptions": {
            "financial_rules": "Stated SIH problem parameters; deterministic scheme and repayment rules.",
            "public_data_proxies": "No live public datasets are connected. Demand and competition are prototype proxies.",
            "geospatial_assumptions": "5–10 km catchment is a planning assumption, not GIS analysis.",
            "business_assumptions": "Category turnover, operating-cost and working-capital ratios are illustrative planning assumptions.",
            "prototype_assumptions": "Scenarios adjust only the listed revenue/cost assumptions; they are not forecasts.",
        },
    }
