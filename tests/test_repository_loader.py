import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzer.repository_loader import (
    clone_repository,
    normalize_repository_url,
)


class NormalizeRepositoryUrlTests(unittest.TestCase):
    def test_normalizes_repository_and_branch_page_urls(self):
        urls = (
            "https://github.com/owner/project",
            "https://github.com/owner/project.git/",
            "https://github.com/owner/project/tree/main",
            "github.com/owner/project/tree/feature/my-branch",
            "git@github.com:owner/project.git",
        )

        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(
                    normalize_repository_url(url),
                    "https://github.com/owner/project.git",
                )

    def test_rejects_urls_outside_github(self):
        for url in (
            "",
            "https://example.com/owner/project",
            "https://github.com/",
            "https://github.com/owner",
            "https://user:password@github.com/owner/project",
        ):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    normalize_repository_url(url)


class CloneRepositoryTests(unittest.TestCase):
    def test_clone_failure_preserves_previous_repository(self):
        with tempfile.TemporaryDirectory() as parent:
            destination = Path(parent) / "repository"
            destination.mkdir()
            marker = destination / "existing.txt"
            marker.write_text("previous repository", encoding="utf-8")

            with patch(
                "analyzer.repository_loader.Repo.clone_from",
                side_effect=RuntimeError("clone failed"),
            ):
                with self.assertRaisesRegex(RuntimeError, "clone failed"):
                    clone_repository(
                        "https://github.com/owner/project",
                        str(destination),
                        raise_errors=True,
                    )

            self.assertEqual(marker.read_text(encoding="utf-8"), "previous repository")
            self.assertEqual(
                [path.name for path in Path(parent).iterdir()],
                ["repository"],
            )

    def test_clone_uses_shallow_options_and_replaces_previous_repository(self):
        with tempfile.TemporaryDirectory() as parent:
            destination = Path(parent) / "repository"
            destination.mkdir()
            (destination / "old.txt").write_text("old", encoding="utf-8")

            def fake_clone(url, target, **kwargs):
                self.assertEqual(url, "https://github.com/owner/project.git")
                self.assertEqual(
                    kwargs["multi_options"],
                    ["--depth=1", "--single-branch"],
                )
                Path(target, "new.txt").write_text("new", encoding="utf-8")

            with patch(
                "analyzer.repository_loader.Repo.clone_from",
                side_effect=fake_clone,
            ):
                self.assertTrue(
                    clone_repository(
                        "https://github.com/owner/project/tree/main",
                        str(destination),
                        raise_errors=True,
                    )
                )

            self.assertFalse((destination / "old.txt").exists())
            self.assertEqual(
                (destination / "new.txt").read_text(encoding="utf-8"),
                "new",
            )
            self.assertEqual(
                [path.name for path in Path(parent).iterdir()],
                ["repository"],
            )


if __name__ == "__main__":
    unittest.main()
