import unittest

from fastapi.testclient import TestClient

from app.main import app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_calculate_valid_request(self):
        response = self.client.post("/api/financial/calculate", json={
            "location": "Vadodara, Gujarat", "business_category": "dairy", "margin_capital": 100000
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["loan_amount"], 900000)
        self.assertEqual(len(response.json()["analysis"]["scenarios"]), 3)

    def test_calculate_rejects_missing_location(self):
        response = self.client.post("/api/financial/calculate", json={
            "location": "", "business_category": "dairy", "margin_capital": 100000
        })
        self.assertEqual(response.status_code, 422)

    def test_calculate_rejects_zero_margin(self):
        response = self.client.post("/api/financial/calculate", json={
            "location": "Vadodara, Gujarat", "business_category": "dairy", "margin_capital": 0
        })
        self.assertEqual(response.status_code, 422)

    def test_categories_and_schemes(self):
        self.assertEqual(self.client.get("/api/business-categories").status_code, 200)
        self.assertEqual(len(self.client.get("/api/schemes").json()), 2)

    def test_ai_without_key_uses_grounded_demo_advisor(self):
        response = self.client.post("/api/ai/chat", json={"message": "Explain", "financial_context": {}})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mode"], "demo")
        self.assertTrue(response.json()["reply"])
