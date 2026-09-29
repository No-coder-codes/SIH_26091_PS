import unittest
from decimal import Decimal

from app.financial.engine import calculate


class FinancialEngineTests(unittest.TestCase):
    def test_term_loan_demo_scenario(self):
        result = calculate(100000)
        self.assertEqual(result.project_cost, Decimal("1000000.00"))
        self.assertEqual(result.loan_amount, Decimal("900000.00"))
        self.assertEqual(result.scheme, "Term Loan Scheme")
        self.assertEqual(result.moratorium_months, 6)
        self.assertEqual(len(result.repayment_schedule), 28)

    def test_micro_scheme(self):
        result = calculate(10000)
        self.assertEqual(result.scheme, "Micro Finance Scheme")
        self.assertEqual(result.loan_amount, Decimal("90000.00"))
        self.assertEqual(result.tenure_years, 3)

    def test_cap_is_enforced(self):
        # ₹14,000 implies ₹1,40,000: still Micro, but 90% is ₹1,26,000.
        result = calculate(14000)
        self.assertEqual(result.project_cost, Decimal("140000.00"))
        self.assertEqual(result.scheme, "Micro Finance Scheme")
        self.assertEqual(result.loan_amount, Decimal("125000.00"))
        self.assertTrue(result.cap_applied)

    def test_outside_range(self):
        result = calculate(600000)
        self.assertEqual(result.status, "outside_range")
        self.assertIsNone(result.loan_amount)

    def test_boundary_micro_below_threshold(self):
        # Margin ₹13,999 -> Project cost ₹1,39,990 <= ₹1,40,000 (Micro Finance Scheme)
        result = calculate(13999)
        self.assertEqual(result.project_cost, Decimal("139990.00"))
        self.assertEqual(result.scheme, "Micro Finance Scheme")
        self.assertEqual(result.loan_amount, Decimal("125000.00")) # 90% is 125,991, capped at 125,000
        self.assertTrue(result.cap_applied)

    def test_boundary_micro_exact_threshold(self):
        # Margin ₹14,000 -> Project cost ₹1,40,000 == ₹1,40,000 (Micro Finance Scheme)
        result = calculate(14000)
        self.assertEqual(result.project_cost, Decimal("140000.00"))
        self.assertEqual(result.scheme, "Micro Finance Scheme")
        self.assertEqual(result.loan_amount, Decimal("125000.00")) # 90% is 126,000, capped at 125,000
        self.assertTrue(result.cap_applied)

    def test_boundary_term_loan_start_threshold(self):
        # Margin ₹14,000.01 -> Project cost ₹1,40,000.10 > ₹1,40,000 (Term Loan Scheme)
        result = calculate("14000.01")
        self.assertEqual(result.project_cost, Decimal("140000.10"))
        self.assertEqual(result.scheme, "Term Loan Scheme")
        self.assertEqual(result.loan_amount, Decimal("126000.09"))
        self.assertFalse(result.cap_applied)

    def test_boundary_term_loan_near_max(self):
        # Margin ₹4,99,999.90 -> Project cost ₹49,99,999.00 <= ₹50,00,000 (Term Loan Scheme)
        result = calculate("499999.90")
        self.assertEqual(result.project_cost, Decimal("4999999.00"))
        self.assertEqual(result.scheme, "Term Loan Scheme")
        self.assertEqual(result.loan_amount, Decimal("4499999.10"))

    def test_boundary_term_loan_exact_max(self):
        # Margin ₹5,00,000 -> Project cost ₹50,00,000 == ₹50,00,000 (Term Loan Scheme)
        result = calculate(500000)
        self.assertEqual(result.project_cost, Decimal("5000000.00"))
        self.assertEqual(result.scheme, "Term Loan Scheme")
        self.assertEqual(result.loan_amount, Decimal("4500000.00")) # 90% is 4,500,000

    def test_boundary_outside_range_threshold(self):
        # Margin ₹5,00,000.01 -> Project cost ₹50,00,000.10 > ₹50,00,000 (outside_range)
        result = calculate("500000.01")
        self.assertEqual(result.status, "outside_range")
        self.assertIsNone(result.loan_amount)

    def test_zero_margin(self):
        with self.assertRaises(ValueError):
            calculate(0)

    def test_negative_margin(self):
        with self.assertRaises(ValueError):
            calculate(-5000)

    def test_invalid_string_margin(self):
        with self.assertRaises(ValueError):
            calculate("invalid_text")

    def test_decimal_margin(self):
        result = calculate(10000.50)
        self.assertEqual(result.project_cost, Decimal("100005.00"))
        self.assertEqual(result.scheme, "Micro Finance Scheme")
        self.assertEqual(result.loan_amount, Decimal("90004.50"))


if __name__ == "__main__":
    unittest.main()
