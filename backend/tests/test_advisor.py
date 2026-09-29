import unittest

from app.financial.engine import calculate
from app.services.advisor import classify_intent, demo_advisor_reply
from app.services.feasibility import analyse_feasibility


class AdvisorIntentTests(unittest.TestCase):
    def setUp(self):
        financial = calculate(100000).payload()
        financial["location"] = "Vadodara, Gujarat"
        financial["business_category"] = "dairy"
        financial["analysis"] = analyse_feasibility("dairy", financial, "Vadodara, Gujarat")
        self.context = financial

    def test_intent_classification(self):
        self.assertEqual(classify_intent("Why was this scheme selected?"), "scheme")
        self.assertEqual(classify_intent("How was the financing amount calculated?"), "financing")
        self.assertEqual(classify_intent("Explain the repayment structure."), "repayment")
        self.assertEqual(classify_intent("What happens during the moratorium?"), "moratorium")
        self.assertEqual(classify_intent("What are the key risks?"), "risk")
        self.assertEqual(classify_intent("What happens in the stress scenario?"), "scenario")
        self.assertEqual(classify_intent("How much working capital do I need?"), "working_capital")
        self.assertEqual(classify_intent("What assumptions drive the result?"), "assumptions")
        self.assertEqual(classify_intent("Summarise my result."), "summary")
        self.assertEqual(classify_intent("loan kaise calculate hua?"), "financing")
        self.assertEqual(classify_intent("scheme kyu mili?"), "scheme")
        self.assertEqual(classify_intent("What is the capital of France?"), "unknown")

    def test_advisor_questions_produce_distinct_grounded_replies(self):
        questions = [
            "Why was this scheme selected?",
            "How was the financing amount calculated?",
            "Explain the repayment structure.",
            "What happens during the moratorium?",
            "What happens in the stress scenario?",
            "What are the key risks?",
            "What assumptions drive the result?",
            "Summarise my result."
        ]
        replies = set()
        for q in questions:
            reply = demo_advisor_reply(q, self.context)
            self.assertTrue(len(reply) > 20)
            replies.add(reply)
        # Verify that different questions produced distinct responses
        self.assertEqual(len(replies), len(questions))

    def test_unsupported_question_returns_explicit_disclaimer(self):
        reply = demo_advisor_reply("What is the population of Paris?", self.context)
        self.assertIn("don't have verified data", reply.lower())


if __name__ == "__main__":
    unittest.main()
