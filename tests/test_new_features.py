import unittest
import tempfile
import json
import os
import shutil
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app, SESSIONS_DIRECTORY
from analyzer.impact_analyzer import analyze_change_impact
from analyzer.task_guidance import generate_task_guidance
from analyzer.repository_analyzer import detect_tech_stack, generate_codebase_map, scan_sensitive_files

class NewFeaturesApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.headers = {"X-Session-ID": "a" * 32}
        self.session_dir = os.path.join(SESSIONS_DIRECTORY, "a" * 32)
        os.makedirs(self.session_dir, exist_ok=True)

        # Copy data/project_info.json and cloned_repo into session if exists
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        src_json = os.path.join(data_dir, "project_info.json")
        dest_json = os.path.join(self.session_dir, "project_info.json")
        if os.path.exists(src_json):
            shutil.copy(src_json, dest_json)
        else:
            sample_info = {
                "project_name": "chess",
                "statistics": {"files": 3, "directories": 0, "total_classes": 2, "total_functions": 10},
                "languages": {"C++": 1},
                "tech_stack": {"languages": ["C++"], "frameworks": ["STL"]},
                "codebase_map": {"modules": [], "entry_points": []},
                "knowledge_concentration": {"contributors": [], "module_ownership": []},
                "code_evolution_timeline": {"events": []},
                "security_scan": {"status": "Secure"},
                "important_files": [],
                "dependencies": {"python_requirements": []},
                "readme": "# Chess"
            }
            with open(dest_json, "w", encoding="utf-8") as f:
                json.dump(sample_info, f)

        src_repo = os.path.join(data_dir, "cloned_repo")
        dest_repo = os.path.join(self.session_dir, "cloned_repo")
        if os.path.exists(src_repo) and not os.path.exists(dest_repo):
            shutil.copytree(src_repo, dest_repo)

    def test_health_check_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "Codebase Onboarding Companion")

    def test_tech_stack_endpoint(self):
        response = self.client.get("/tech-stack", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertIn("tech_stack", response.json())

    def test_codebase_map_endpoint(self):
        response = self.client.get("/codebase-map", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        codebase_map = response.json()["codebase_map"]
        self.assertIn("modules", codebase_map)
        self.assertIn("entry_points", codebase_map)

    def test_knowledge_concentration_endpoint(self):
        response = self.client.get("/knowledge-concentration", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        kc = response.json()["knowledge_concentration"]
        self.assertIn("contributors", kc)
        self.assertIn("module_ownership", kc)

    def test_code_evolution_timeline_endpoint(self):
        response = self.client.get("/code-evolution-timeline", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertIn("events", response.json())

    def test_change_preview_endpoint(self):
        response = self.client.post(
            "/change-preview",
            json={"file_path": "chess.h", "symbol": "Board"},
            headers=self.headers,
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
            json={"task": "Fix checkmate detection logic"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("primary_file", data)
        self.assertIn("action_plan", data)

    def test_management_overview_endpoint(self):
        response = self.client.get("/management/overview", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("aggregate_reporting", data)
        self.assertIn("privacy_safeguard", data["aggregate_reporting"])

    def test_senior_review_endpoints(self):
        # GET initial
        get_res = self.client.get("/senior/review", headers=self.headers)
        self.assertEqual(get_res.status_code, 200)

        # POST review approval
        post_res = self.client.post(
            "/senior/review",
            json={"approved": True, "feedback": "Looks accurate for onboarding.", "approved_by": "Lead Dev"},
            headers=self.headers,
        )
        self.assertEqual(post_res.status_code, 200)
        self.assertTrue(post_res.json()["success"])

        # GET updated
        get_res2 = self.client.get("/senior/review", headers=self.headers)
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
