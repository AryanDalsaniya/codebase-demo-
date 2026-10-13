import os
import re

def generate_task_guidance(directory: str, project_info: dict, task_description: str) -> dict:
    """
    FR-13: Task-to-Code Guidance.
    Given a short task description, points the junior developer to the relevant
    module, files, and functions to start from.
    """
    task = task_description.strip()
    if not task:
        return {
            "success": False,
            "message": "Task description cannot be empty."
        }

    tokens = [t.lower() for t in re.findall(r"[A-Za-z0-9_]+", task) if len(t) >= 3]

    files_scored = []
    py_files = project_info.get("python_analysis", {}).get("files", [])
    py_file_map = {f["file"]: f for f in py_files}

    # Walk directory to find files
    for root, dirs, filenames in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "node_modules", "venv", ".venv", "build", "dist"}]
        for fname in filenames:
            rel = os.path.relpath(os.path.join(root, fname), directory).replace("\\", "/")
            fname_lower = fname.lower()
            rel_lower = rel.lower()

            score = 0
            matched_symbols = []

            # Check filename against task tokens
            for tok in tokens:
                if tok in fname_lower:
                    score += 15
                elif tok in rel_lower:
                    score += 8

            # Check python AST symbols if available
            if rel in py_file_map:
                info = py_file_map[rel]
                for cls_name in info.get("classes", []):
                    for tok in tokens:
                        if tok in cls_name.lower():
                            score += 12
                            matched_symbols.append(f"class {cls_name}")
                for fn_name in info.get("functions", []):
                    for tok in tokens:
                        if tok in fn_name.lower():
                            score += 10
                            matched_symbols.append(f"function {fn_name}")

            # Read file snippets if small or text file
            ext = os.path.splitext(fname)[1].lower()
            if ext in {".py", ".cpp", ".h", ".hpp", ".c", ".js", ".ts", ".html", ".css", ".md", ".json"}:
                try:
                    with open(os.path.join(root, fname), "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read(50000).lower()
                    for tok in tokens:
                        count = content.count(tok)
                        if count > 0:
                            score += min(count * 2, 12)
                except OSError:
                    pass

            if score > 0:
                files_scored.append({
                    "file": rel,
                    "score": score,
                    "matched_symbols": list(set(matched_symbols)),
                    "is_test": "test" in rel_lower
                })

    files_scored.sort(key=lambda x: x["score"], reverse=True)

    # Separate code files vs test files
    code_files = [f for f in files_scored if not f["is_test"]]
    test_files = [f for f in files_scored if f["is_test"]]

    primary_file = code_files[0]["file"] if code_files else (files_scored[0]["file"] if files_scored else "README.md")
    primary_module = os.path.dirname(primary_file) or "Root"

    steps = [
        f"1. Open `{primary_file}` to understand the existing implementation and signatures.",
        f"2. Inspect the relevant symbols or functions ({', '.join(code_files[0]['matched_symbols']) if code_files and code_files[0]['matched_symbols'] else 'entry points in ' + primary_file}).",
        f"3. Run the Change Preview tool on `{primary_file}` before saving changes to verify what other files rely on it.",
    ]

    if test_files:
        steps.append(f"4. Review and update corresponding tests in `{test_files[0]['file']}` to prevent regressions.")
    else:
        steps.append("4. Add unit test coverage for the changes made.")

    steps.append("5. Submit your pull request for senior developer review once all checks pass.")

    return {
        "success": True,
        "task": task,
        "primary_module": primary_module,
        "primary_file": primary_file,
        "relevant_files": code_files[:5],
        "relevant_tests": test_files[:3],
        "action_plan": steps,
    }

