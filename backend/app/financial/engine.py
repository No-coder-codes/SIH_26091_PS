"""Deterministic financial calculations for the Gram Udyog prototype.

The SIH parameters are configured here; no AI code is involved in calculation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

MONEY = Decimal("0.01")

SCHEMES = {
    "micro": {
        "id": "micro",
        "name": "Micro Finance Scheme",
        "min_project_cost": Decimal("0"),
        "max_project_cost": Decimal("140000"),
        "finance_percent": Decimal("0.90"),
        "max_loan": Decimal("125000"),
        "annual_interest_rate": Decimal("0.065"),
        "tenure_years": 3,
        "moratorium_months": 3,
    },
    "term": {
        "id": "term",
        "name": "Term Loan Scheme",
        "min_project_cost": Decimal("140000.01"),
        "max_project_cost": Decimal("5000000"),
        "finance_percent": Decimal("0.90"),
        "max_loan": Decimal("4500000"),
        "annual_interest_rate": Decimal("0.08"),
        "tenure_years": 7,
        "moratorium_months": 6,
    },
}


def money(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value)).quantize(MONEY, rounding=ROUND_HALF_UP)


def select_scheme(project_cost: Decimal) -> Optional[dict]:
    if project_cost <= SCHEMES["micro"]["max_project_cost"]:
        return SCHEMES["micro"]
    if project_cost <= SCHEMES["term"]["max_project_cost"]:
        return SCHEMES["term"]
    return None


@dataclass
class Calculation:
    margin_capital: Decimal
    project_cost: Decimal
    loan_amount: Optional[Decimal]
    required_own_contribution: Decimal
    financing_gap: Optional[Decimal]
    scheme: Optional[str]
    scheme_id: Optional[str]
    interest_rate: Optional[Decimal]
    tenure_years: Optional[int]
    moratorium_months: Optional[int]
    repayment_start: Optional[str]
    quarterly_payment: Optional[Decimal]
    total_repayment: Optional[Decimal]
    total_interest: Optional[Decimal]
    cap_applied: bool
    status: str
    message: str
    repayment_schedule: list[dict]

    def payload(self) -> dict:
        result = asdict(self)
        for key, value in result.items():
            if isinstance(value, Decimal):
                result[key] = float(value)
        result["repayment_schedule"] = [
            {k: float(v) if isinstance(v, Decimal) else v for k, v in row.items()}
            for row in self.repayment_schedule
        ]
        return result


def generate_quarterly_schedule(principal: Decimal, annual_rate: Decimal, tenure_years: int, moratorium_months: int) -> tuple[list[dict], Decimal, Decimal, Decimal]:
    """Monthly reducing-balance EMI after a no-payment, capitalized-interest moratorium.

    The monthly payments are aggregated into display-only quarters. This is a prototype
    assumption, not an official lender schedule.
    """
    monthly_rate = annual_rate / Decimal("12")
    balance = principal
    accrued = Decimal("0")
    for month in range(1, moratorium_months + 1):
        interest = money(balance * monthly_rate)
        accrued += interest
        balance += interest

    months = tenure_years * 12
    if monthly_rate == 0:
        emi = money(balance / months)
    else:
        factor = (Decimal("1") + monthly_rate) ** months
        emi = money(balance * monthly_rate * factor / (factor - Decimal("1")))

    schedule: list[dict] = []
    total_paid = Decimal("0")
    # Group three calculated monthly instalments into quarterly presentation rows.
    for quarter in range(1, (months // 3) + 1):
        opening = balance
        q_payment = q_interest = q_principal = Decimal("0")
        for _ in range(3):
            interest = money(balance * monthly_rate)
            payment = min(emi, money(balance + interest))
            principal_paid = money(payment - interest)
            balance = money(balance - principal_paid)
            q_payment += payment
            q_interest += interest
            q_principal += principal_paid
        total_paid += q_payment
        schedule.append({
            "quarter": quarter,
            "period": f"Quarter {quarter}",
            "opening_balance": money(opening),
            "payment": money(q_payment),
            "principal_paid": money(q_principal),
            "interest_paid": money(q_interest),
            "closing_balance": max(money(balance), Decimal("0")),
        })
    # Rounding makes the final residual tiny; correct it on the final row.
    if balance != 0 and schedule:
        final = schedule[-1]
        adjustment = balance
        final["payment"] = money(final["payment"] + adjustment)
        final["principal_paid"] = money(final["principal_paid"] + adjustment)
        final["closing_balance"] = Decimal("0")
        total_paid += adjustment
    total_interest = money(total_paid - principal)
    return schedule, money(total_paid), total_interest, money(schedule[0]["payment"])


def calculate(margin_capital: Decimal | int | float | str) -> Calculation:
    try:
        margin = money(margin_capital)
    except Exception as error:
        raise ValueError(f"Invalid margin capital value: '{margin_capital}'. Must be a valid positive number.") from error
    if margin <= 0:
        raise ValueError("Available margin capital must be greater than ₹0.")
    project_cost = money(margin * 10)
    scheme = select_scheme(project_cost)
    if not scheme:
        return Calculation(
            margin_capital=margin,
            project_cost=project_cost,
            loan_amount=None,
            required_own_contribution=margin,
            financing_gap=None,
            scheme=None,
            scheme_id=None,
            interest_rate=None,
            tenure_years=None,
            moratorium_months=None,
            repayment_start=None,
            quarterly_payment=None,
            total_repayment=None,
            total_interest=None,
            cap_applied=False,
            status="outside_range",
            message="The implied project cost is above the stated scheme range of ₹50,00,000.",
            repayment_schedule=[],
        )
    theoretical_loan = money(project_cost * scheme["finance_percent"])
    loan = min(theoretical_loan, scheme["max_loan"])
    cap_applied = loan < theoretical_loan
    required_own = money(project_cost - loan)
    gap = money(max(Decimal("0"), required_own - margin))
    schedule, total_repayment, total_interest, quarterly_payment = generate_quarterly_schedule(
        loan, scheme["annual_interest_rate"], scheme["tenure_years"], scheme["moratorium_months"]
    )
    cap_note = f" The scheme maximum loan cap of ₹{scheme['max_loan']:,.0f} applies." if cap_applied else ""
    return Calculation(
        margin, project_cost, loan, required_own, gap, scheme["name"], scheme["id"], scheme["annual_interest_rate"],
        scheme["tenure_years"], scheme["moratorium_months"], f"After {scheme['moratorium_months']} months",
        quarterly_payment, total_repayment, total_interest, cap_applied, "eligible",
        f"Project cost is routed to the {scheme['name']}.{cap_note}", schedule,
    )


def schemes_payload() -> list[dict]:
    return [{k: (float(v) if isinstance(v, Decimal) else v) for k, v in scheme.items()} for scheme in SCHEMES.values()]
