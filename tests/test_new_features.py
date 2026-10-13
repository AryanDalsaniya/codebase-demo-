import unittest
import tempfile
import json
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from analyzer.impact_analyzer import analyze_change_impact
from analyzer.task_guidance import generate_task_guidance
from analyzer.repository_analyzer import detect_tech_stack, generate_codebase_map, scan_sensitive_files

class NewFeaturesApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "Codebase Onboarding Companion")

    def test_tech_stack_endpoint(self):
        response = self.client.get("/tech-stack")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertIn("tech_stack", response.json())

    def test_codebase_map_endpoint(self):
        response = self.client.get("/codebase-map")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        codebase_map = response.json()["codebase_map"]
        self.assertIn("modules", codebase_map)
        self.assertIn("entry_points", codebase_map)

    def test_knowledge_concentration_endpoint(self):
        response = self.client.get("/knowledge-concentration")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        kc = response.json()["knowledge_concentration"]
        self.assertIn("contributors", kc)
        self.assertIn("module_ownership", kc)

    def test_code_evolution_timeline_endpoint(self):
        response = self.client.get("/code-evolution-timeline")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertIn("events", response.json())

    def test_change_preview_endpoint(self):
        response = self.client.post(
            "/change-preview",
            json={"file_path": "chess.h", "symbol": "Board"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("risk_level", data)
        self.assertIn("direct_dependents", data)
        self.assertIn("affected_tests", data)

    def test_task_guidance_endpoint(self):
        response = self.client.post(
            "/task-guidance",
            json={"task": "Fix checkmate detection logic"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("primary_file", data)
        self.assertIn("action_plan", data)

    def test_management_overview_endpoint(self):
        response = self.client.get("/management/overview")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("aggregate_reporting", data)
        self.assertIn("privacy_safeguard", data["aggregate_reporting"])

    def test_senior_review_endpoints(self):
        # GET initial
        get_res = self.client.get("/senior/review")
        self.assertEqual(get_res.status_code, 200)

        # POST review approval
        post_res = self.client.post(
            "/senior/review",
            json={"approved": True, "feedback": "Looks accurate for onboarding.", "approved_by": "Lead Dev"}
        )
        self.assertEqual(post_res.status_code, 200)
        self.assertTrue(post_res.json()["success"])

        # GET updated
        get_res2 = self.client.get("/senior/review")
        self.assertEqual(get_res2.status_code, 200)
        self.assertTrue(get_res2.json()["is_approved"])

    def test_sensitive_files_scan_and_exclusion(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / ".env").write_text("SECRET_KEY=12345", encoding="utf-8")
            (temp_path / "id_rsa").write_text("PRIVATE_KEY", encoding="utf-8")
            (temp_path / "app.py").write_text("print('hello')", encoding="utf-8")

            scan = scan_sensitive_files(temp_dir)
            self.assertEqual(scan["count"], 2)
            self.assertTrue(any(".env" in f for f in scan["sensitive_files_detected"]))
            self.assertTrue(any("id_rsa" in f for f in scan["sensitive_files_detected"]))

if __name__ == "__main__":
    unittest.main()

