import unittest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app, get_session_paths


class AnalyzeEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.headers = {"X-Session-ID": "a" * 32}

    def test_invalid_repository_url_returns_actionable_client_error(self):
        response = self.client.post(
            "/analyze",
            json={"repo_url": "https://example.com/owner/repository"},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 422)
        self.assertIn("public GitHub repository URL", response.json()["detail"])

    def test_clone_failure_is_not_returned_as_success(self):
        with patch(
            "backend.main.clone_repository",
            side_effect=RuntimeError("network unavailable"),
        ):
            response = self.client.post(
                "/analyze",
                json={"repo_url": "https://github.com/owner/repository"},
                headers=self.headers,
            )

        self.assertEqual(response.status_code, 502)
        self.assertIn("public", response.json()["detail"])
        self.assertNotIn("success", response.json())

    def test_summary_reads_existing_bom_marked_project_info(self):
        project_info = {
            "project_name": "chess",
            "statistics": {"files": 5, "directories": 2},
            "languages": {"Python": 5},
            "important_files": [],
            "python_analysis": {
                "total_classes": 1,
                "total_functions": 2,
            },
            "dependencies": {"python_requirements": []},
            "readme": "# Chess",
        }

        with tempfile.TemporaryDirectory() as directory:
            session_directory = Path(directory) / ("a" * 32)
            session_directory.mkdir()
            project_info_path = session_directory / "project_info.json"
            project_info_path.write_text(
                json.dumps(project_info),
                encoding="utf-8-sig",
            )

            with patch("backend.main.SESSIONS_DIRECTORY", directory):
                response = self.client.get("/summary", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["project_name"], "chess")
        self.assertEqual(response.json()["readme"], "# Chess")

    def test_browser_sessions_have_separate_repository_paths(self):
        first_paths = get_session_paths("a" * 32)
        second_paths = get_session_paths("b" * 32)

        self.assertNotEqual(first_paths, second_paths)

    def test_repository_api_requires_a_browser_session(self):
        response = self.client.get("/summary")

        self.assertEqual(response.status_code, 422)

    def test_configured_app_password_protects_api_but_not_health_check(self):
        with patch.dict(os.environ, {"APP_PASSWORD": "test-password"}):
            protected = self.client.get(
                "/summary",
                headers=self.headers,
            )
            authorized = self.client.get(
                "/summary",
                headers={
                    **self.headers,
                    "X-App-Password": "test-password",
                },
            )
            health = self.client.get("/healthz")

        self.assertEqual(protected.status_code, 401)
        self.assertNotEqual(authorized.status_code, 401)
        self.assertEqual(health.status_code, 200)

    def test_onboarding_guide_explains_missing_openai_key(self):
        project_info = {
            "project_name": "chess",
            "statistics": {"files": 1, "directories": 0},
            "languages": {"C++": 1},
        }

        with tempfile.TemporaryDirectory() as directory:
            session_directory = Path(directory) / ("a" * 32)
            session_directory.mkdir()
            (session_directory / "project_info.json").write_text(
                json.dumps(project_info),
                encoding="utf-8",
            )

            with (
                patch("backend.main.SESSIONS_DIRECTORY", directory),
                patch.dict(os.environ, {"OPENAI_API_KEY": ""}),
            ):
                response = self.client.get(
                    "/onboarding-guide",
                    headers=self.headers,
                )

        self.assertEqual(response.status_code, 503)
        self.assertIn("OPENAI_API_KEY", response.json()["detail"])

    def test_root_serves_frontend(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Codebase Onboarding Companion", response.text)

    def test_root_serves_frontend_assets(self):
        script = self.client.get("/script.js")
        stylesheet = self.client.get("/style.css")

        self.assertEqual(script.status_code, 200)
        self.assertEqual(stylesheet.status_code, 200)
        self.assertIn("X-Session-ID", script.text)


if __name__ == "__main__":
    unittest.main()
