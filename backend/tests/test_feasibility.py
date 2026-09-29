import unittest

from app.financial.engine import calculate
from app.services.feasibility import analyse_feasibility


class FeasibilityTests(unittest.TestCase):
    def setUp(self):
        self.financial = calculate(100000).payload()
        self.analysis = analyse_feasibility("dairy", self.financial, "Vadodara, Gujarat")

    def test_deterministic_economics_and_scenarios(self):
        economics = self.analysis["business_economics"]
        self.assertEqual(economics["estimated_monthly_revenue"], 180000.0)
        self.assertEqual(economics["working_capital_requirement"], 21600.0)
        self.assertEqual([item["name"] for item in self.analysis["scenarios"]], ["Conservative", "Expected", "Stress"])

    def test_stress_reduces_cash_for_debt_service(self):
        expected = self.analysis["scenarios"][1]
        stress = self.analysis["scenarios"][2]
        self.assertLess(stress["cash_available_for_debt_service"], expected["cash_available_for_debt_service"])

    def test_assumptions_are_explicit(self):
        self.assertIn("No live public datasets", self.analysis["assumptions"]["public_data_proxies"])
