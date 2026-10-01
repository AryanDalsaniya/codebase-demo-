import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app


class AnalyzeEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_invalid_repository_url_returns_actionable_client_error(self):
        response = self.client.post(
            "/analyze",
            json={"repo_url": "https://example.com/owner/repository"},
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
            project_info_path = Path(directory) / "project_info.json"
            project_info_path.write_text(
                json.dumps(project_info),
                encoding="utf-8-sig",
            )

            with patch("backend.main.PROJECT_INFO_PATH", str(project_info_path)):
                response = self.client.get("/summary")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["project_name"], "chess")


if __name__ == "__main__":
    unittest.main()
