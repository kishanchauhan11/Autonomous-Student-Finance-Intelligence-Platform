import sys
import os
import unittest
import unittest.mock
from fastapi.testclient import TestClient

# Adjust python path to import main and backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app

class TestPlatformIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_get_student_arjun(self):
        response = self.client.get("/api/student/STU-2021-4892")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["student"]["name"], "Arjun Shah")
        self.assertEqual(data["student"]["currency"], "INR")

    def test_get_student_sarah(self):
        response = self.client.get("/api/student/STU-2022-1082")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["student"]["name"], "Sarah Connor")
        self.assertEqual(data["student"]["currency"], "USD")

    def test_pay_transaction_success(self):
        payload = {
            "student_id": "STU-2021-4892",
            "amount": 10000.0,
            "category": "Tuition Fee Sem 7",
            "method": "Net Banking"
        }
        response = self.client.post("/api/transactions/pay", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["transaction"]["student_id"], "STU-2021-4892")
        self.assertEqual(data["transaction"]["amount"], 10000.0)
        self.assertEqual(data["transaction"]["status"], "APPROVED")

    def test_pay_transaction_invalid_student(self):
        payload = {
            "student_id": "STU-INVALID",
            "amount": 1000.0,
            "category": "Tuition Fee",
            "method": "Net Banking"
        }
        response = self.client.post("/api/transactions/pay", json=payload)
        self.assertEqual(response.status_code, 404)

    def test_download_loan_demand_pdf(self):
        response = self.client.get("/downloads/loan-demand-STU-2021-4892.pdf")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertTrue(b"PDF" in response.content)
        self.assertTrue(len(response.content) > 0)

        response = self.client.get("/downloads/loan-demand-STU-2022-1082.pdf")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertTrue(len(response.content) > 0)

    def test_download_loan_demand_pdf_invalid_student(self):
        response = self.client.get("/downloads/loan-demand-STU-INVALID.pdf")
        self.assertEqual(response.status_code, 404)

    @unittest.mock.patch("requests.Session.post")
    def test_nvidia_client_timeout_fallback(self, mock_post):
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")
        
        payload = {
            "student_id": "STU-2021-4892",
            "message": "What is my current payable fee balance?",
            "history": []
        }
        response = self.client.post("/api/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data["safe"])
        self.assertEqual(data["agent"], "Root Finance Orchestrator")
        self.assertEqual(data["intent"], "PAYMENT")
        self.assertIn("Offline Fallback Mode", data["response"])
        self.assertIn("Arjun Shah", data["response"])

    @unittest.mock.patch("requests.Session.post")
    def test_nvidia_client_timeout_fallback_sarah(self, mock_post):
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")
        
        payload = {
            "student_id": "STU-2022-1082",
            "message": "Where is my refund request status?",
            "history": []
        }
        response = self.client.post("/api/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data["safe"])
        self.assertEqual(data["agent"], "Root Finance Orchestrator")
        self.assertEqual(data["intent"], "REFUND")
        self.assertIn("Offline Fallback Mode", data["response"])
        self.assertIn("Sarah Connor", data["response"])
        self.assertIn("Refund Status", data["response"])

if __name__ == "__main__":
    unittest.main()
