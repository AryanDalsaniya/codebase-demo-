import tempfile
import unittest
from pathlib import Path

from analyzer.repository_analyzer import (
    analyze_repository,
    analyze_python_code,
    build_file_tree,
    read_readme,
    save_project_info,
)


class RepositoryAnalyzerTests(unittest.TestCase):
    def test_skips_generated_directories_and_counts_python_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text(
                "class App:\n    def run(self):\n        pass\n",
                encoding="utf-8",
            )
            (root / "node_modules").mkdir()
            (root / "node_modules" / "ignored.py").write_text(
                "class Generated:\n    pass\n",
                encoding="utf-8",
            )
            (root / ".git").mkdir()
            (root / ".git" / "ignored.js").write_text("ignored", encoding="utf-8")

            files, directories, languages = analyze_repository(directory)
            python_analysis = analyze_python_code(directory)
            tree = build_file_tree(directory)

            self.assertEqual(files, 1)
            self.assertEqual(directories, 1)
            self.assertEqual(languages, {"Python": 1})
            self.assertEqual(python_analysis["total_classes"], 1)
            self.assertEqual(python_analysis["total_functions"], 1)
            self.assertEqual([entry["name"] for entry in tree], ["src"])
            self.assertEqual(tree[0]["children"][0]["name"], "app.py")

    def test_reads_utf8_bom_readme(self):
        with tempfile.TemporaryDirectory() as directory:
            readme = Path(directory) / "README.md"
            readme.write_bytes(b"\xef\xbb\xbf# Caf\xc3\xa9")

            self.assertEqual(read_readme(directory), "# Café")

    def test_saves_project_info_without_a_bom(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "project_info.json"
            save_project_info({"project_name": "chess"}, output)

            self.assertFalse(output.read_bytes().startswith(b"\xef\xbb\xbf"))


if __name__ == "__main__":
    unittest.main()
