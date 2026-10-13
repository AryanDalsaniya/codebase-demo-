import os
import re
import ast

# Directories to ignore during impact scanning
IGNORED_DIRECTORIES = {
    ".git",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "build",
    "dist",
    ".idea",
    ".vscode",
}

# Sensitive files to exclude from analysis
SENSITIVE_PATTERNS = [
    re.compile(r"^\.env(\..+)?$", re.IGNORECASE),
    re.compile(r".*\.(pem|key|pkcs12|pfx)$", re.IGNORECASE),
    re.compile(r".*(id_rsa|id_ed25519).*", re.IGNORECASE),
]

def is_sensitive(filename: str) -> bool:
    name = os.path.basename(filename)
    return any(pattern.match(name) for pattern in SENSITIVE_PATTERNS)

def is_test_file(file_path: str) -> bool:
    norm = file_path.replace("\\", "/").lower()
    base = os.path.basename(norm)
    parts = norm.split("/")
    if any(part in {"tests", "test", "__tests__", "spec"} for part in parts):
        return True
    if base.startswith("test_") or base.endswith("_test.py") or base.endswith(".test.js") or base.endswith(".spec.js") or base.endswith("_test.cpp"):
        return True
    return False

def extract_file_references(file_path: str) -> set:
    """Extract imported modules, header includes, and file basenames referenced in a file."""
    references = set()
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except OSError:
        return references

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".py":
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        references.add(alias.name)
                        references.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        references.add(node.module)
                        references.add(node.module.split(".")[0])
                    for alias in node.names:
                        references.add(alias.name)
        except SyntaxError:
            # Fallback to regex for unparseable Python
            for match in re.findall(r"(?:from|import)\s+([a-zA-Z0-9_\.]+)", content):
                references.add(match)
                references.add(match.split(".")[0])

    elif ext in {".c", ".cpp", ".cc", ".cxx", ".h", ".hpp"}:
        for match in re.findall(r'#include\s*["<]([^">]+)[">]', content):
            references.add(os.path.basename(match))
            references.add(os.path.splitext(os.path.basename(match))[0])

    elif ext in {".js", ".jsx", ".ts", ".tsx"}:
        for match in re.findall(r'(?:import|from|require\s*\()\s*[\'"]([^\'"]+)[\'"]', content):
            references.add(os.path.basename(match))
            clean = os.path.splitext(os.path.basename(match))[0]
            references.add(clean)

    # General word token references
    tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", content))
    return references.union(tokens)

def analyze_change_impact(repo_directory: str, target_file: str, symbol: str = None) -> dict:
    """
    FR-14 & US-JD-02: Change Preview / Impact Awareness.
    Surfaces the files, dependencies, and tests likely affected before editing a file or function.
    Distinguishes direct vs indirect usage and flags affected tests.
    """
    target_norm = target_file.strip().replace("\\", "/")
    target_base = os.path.basename(target_norm)
    target_stem = os.path.splitext(target_base)[0]

    all_files = []
    file_references_map = {}

    for root, directories, files in os.walk(repo_directory):
        directories[:] = [d for d in directories if d not in IGNORED_DIRECTORIES]
        for f in files:
            if is_sensitive(f):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, repo_directory).replace("\\", "/")
            all_files.append(rel)
            file_references_map[rel] = extract_file_references(full)

    direct_dependents = []
    indirect_dependents = []
    affected_tests = []

    # Check direct dependents
    for file_rel, refs in file_references_map.items():
        if file_rel == target_norm:
            continue

        is_direct = False
        # Direct check by filename or stem
        if target_base in refs or target_stem in refs:
            is_direct = True
        elif target_norm in refs:
            is_direct = True

        # Check symbol if provided
        if symbol and symbol.strip():
            symbol_clean = symbol.strip()
            if symbol_clean in refs and (is_direct or target_stem in refs):
                is_direct = True

        if is_direct:
            if is_test_file(file_rel):
                affected_tests.append({
                    "file": file_rel,
                    "type": "Direct test dependency",
                    "reason": f"Directly references {target_base}" + (f" and symbol '{symbol}'" if symbol else "")
                })
            else:
                direct_dependents.append({
                    "file": file_rel,
                    "reason": f"Imports or references {target_base}" + (f" (matches symbol '{symbol}')" if symbol else "")
                })

    # Check indirect dependents (depend on direct dependents)
    direct_set = {d["file"] for d in direct_dependents}
    for file_rel, refs in file_references_map.items():
        if file_rel == target_norm or file_rel in direct_set:
            continue

        for direct_file in direct_set:
            direct_base = os.path.basename(direct_file)
            direct_stem = os.path.splitext(direct_base)[0]
            if direct_base in refs or direct_stem in refs:
                if is_test_file(file_rel):
                    if not any(t["file"] == file_rel for t in affected_tests):
                        affected_tests.append({
                            "file": file_rel,
                            "type": "Indirect test dependency",
                            "reason": f"Tests {direct_file}, which directly depends on {target_base}"
                        })
                else:
                    indirect_dependents.append({
                        "file": file_rel,
                        "via": direct_file,
                        "reason": f"Depends on {direct_file}, which references {target_base}"
                    })
                break

    # Determine risk level
    total_dependents = len(direct_dependents) + len(indirect_dependents)
    if total_dependents > 5 or (total_dependents > 0 and len(affected_tests) == 0):
        risk_level = "High"
        risk_color = "#e5484d"
    elif total_dependents >= 2:
        risk_level = "Medium"
        risk_color = "#f76b15"
    else:
        risk_level = "Low"
        risk_color = "#46a758"

    recommendations = []
    if affected_tests:
        test_names = ", ".join([os.path.basename(t["file"]) for t in affected_tests[:3]])
        recommendations.append(f"Run tests before and after making edits: {test_names}.")
    else:
        recommendations.append("No automated test suite was found covering this component. Exercise caution and verify manually.")

    if direct_dependents:
        dep_sample = ", ".join([os.path.basename(d["file"]) for d in direct_dependents[:3]])
        recommendations.append(f"Review call sites in direct dependents: {dep_sample}.")

    recommendations.append("Ensure any signature or interface changes maintain backwards compatibility.")

    return {
        "target_file": target_norm,
        "symbol": symbol or None,
        "risk_level": risk_level,
        "risk_color": risk_color,
        "direct_dependents_count": len(direct_dependents),
        "indirect_dependents_count": len(indirect_dependents),
        "affected_tests_count": len(affected_tests),
        "direct_dependents": direct_dependents,
        "indirect_dependents": indirect_dependents,
        "affected_tests": affected_tests,
        "recommendations": recommendations,
    }

