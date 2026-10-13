import os
import ast
import json
import re
from datetime import datetime

# ---------------------------------------------------------
# Language Detection
# ---------------------------------------------------------

LANGUAGE_EXTENSIONS = {
    ".py": "Python",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".c": "C",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".java": "Java",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".html": "HTML",
    ".css": "CSS",
    ".php": "PHP",
    ".go": "Go",
    ".rs": "Rust",
    ".sh": "Shell",
    ".sql": "SQL",
}

IMPORTANT_FILES = {
    "README.md": "Project documentation",
    "README.txt": "Project documentation",
    "requirements.txt": "Python dependencies",
    "pyproject.toml": "Python project configuration",
    "package.json": "Node.js dependencies and scripts",
    "package-lock.json": "Node.js dependency lock file",
    "pom.xml": "Maven configuration",
    "build.gradle": "Gradle build configuration",
    "CMakeLists.txt": "CMake build configuration",
    "Makefile": "Build automation",
    "Dockerfile": "Docker container configuration",
    "docker-compose.yml": "Docker Compose orchestration",
    "docker-compose.yaml": "Docker Compose orchestration",
    ".gitignore": "Git configuration",
    ".env.example": "Example environment configuration",
}

IGNORED_DIRECTORIES = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "node_modules",
    ".pytest_cache",
    ".tox",
    "build",
    "dist",
    ".next",
    "target",
    ".idea",
    ".vscode",
}

# FR-20, US-SEC-02, DR-03: Sensitive file patterns excluded from AI processing
SENSITIVE_PATTERNS = [
    re.compile(r"^\.env(\..+)?$", re.IGNORECASE),
    re.compile(r".*\.(pem|key|pkcs12|pfx)$", re.IGNORECASE),
    re.compile(r".*(id_rsa|id_ed25519).*", re.IGNORECASE),
    re.compile(r".*(secret|credential|token).*\.(json|yaml|yml|txt|env)$", re.IGNORECASE),
]

def is_sensitive_filename(name: str) -> bool:
    return any(pattern.match(name) for pattern in SENSITIVE_PATTERNS)


# ---------------------------------------------------------
# Basic Repository Analysis
# ---------------------------------------------------------

def analyze_repository(directory):
    file_count = 0
    directory_count = 0
    language_count = {}

    for root, directories, files in os.walk(directory):
        directories[:] = [
            name for name in directories
            if name not in IGNORED_DIRECTORIES
        ]

        directory_count += len(directories)

        for file in files:
            file_count += 1
            extension = os.path.splitext(file)[1].lower()

            if extension in LANGUAGE_EXTENSIONS:
                language = LANGUAGE_EXTENSIONS[extension]
                if language not in language_count:
                    language_count[language] = 0
                language_count[language] += 1

    return file_count, directory_count, language_count


# ---------------------------------------------------------
# Project File Tree
# ---------------------------------------------------------

def build_file_tree(directory):
    tree = []

    try:
        entries = sorted(os.listdir(directory))
    except OSError:
        return tree

    entries = [
        entry for entry in entries
        if entry not in IGNORED_DIRECTORIES
    ]

    for entry in entries:
        path = os.path.join(directory, entry)

        if os.path.isdir(path) and not os.path.islink(path):
            tree.append({
                "name": entry,
                "type": "directory",
                "children": build_file_tree(path)
            })
        else:
            tree.append({
                "name": entry,
                "type": "file"
            })

    return tree


# ---------------------------------------------------------
# Important Files
# ---------------------------------------------------------

def find_important_files(directory):
    found_files = []

    for root, directories, files in os.walk(directory):
        directories[:] = [
            name for name in directories
            if name not in IGNORED_DIRECTORIES
        ]

        for file in files:
            if file in IMPORTANT_FILES:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(
                    full_path,
                    directory
                ).replace("\\", "/")

                found_files.append({
                    "file": relative_path,
                    "description": IMPORTANT_FILES[file]
                })

    return found_files


# ---------------------------------------------------------
# Python File Analysis
# ---------------------------------------------------------

def analyze_python_file(file_path):
    classes = []
    functions = []
    imports = []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            source_code = file.read()
        tree = ast.parse(source_code)
    except (SyntaxError, UnicodeDecodeError, OSError):
        return classes, functions, imports

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return classes, functions, imports


# ---------------------------------------------------------
# Analyze Python Code
# ---------------------------------------------------------

def analyze_python_code(directory):
    python_files = []
    total_classes = 0
    total_functions = 0
    all_imports = set()

    for root, directories, files in os.walk(directory):
        directories[:] = [
            name for name in directories
            if name not in IGNORED_DIRECTORIES
        ]

        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(
                file_path,
                directory
            ).replace("\\", "/")

            classes, functions, imports = analyze_python_file(file_path)

            total_classes += len(classes)
            total_functions += len(functions)

            for imported_module in imports:
                all_imports.add(imported_module)

            python_files.append({
                "file": relative_path,
                "classes": classes,
                "functions": functions,
                "imports": imports
            })

    return {
        "total_classes": total_classes,
        "total_functions": total_functions,
        "imports": sorted(all_imports),
        "files": python_files
    }


# ---------------------------------------------------------
# Multi-Language Symbol Analysis (C/C++, JS/TS)
# ---------------------------------------------------------

def analyze_multi_language_symbols(directory):
    """
    Extracts basic classes and functions for C/C++, JS, and TS files
    so non-Python repositories (like C++ chess) have accurate symbol counts.
    """
    extra_classes = 0
    extra_functions = 0
    symbol_files = []

    class_regex = re.compile(r"\bclass\s+([A-Za-z0-9_]+)\b")
    struct_regex = re.compile(r"\bstruct\s+([A-Za-z0-9_]+)\b")
    # Basic C/C++ or JS function regex
    fn_regex_cpp = re.compile(r"\b[A-Za-z0-9_:<>]+\s+([A-Za-z0-9_]+)\s*\([^;{]*\)\s*(?:const)?\s*[{;]")
    fn_regex_js = re.compile(r"\b(?:function\s+([A-Za-z0-9_]+)|const\s+([A-Za-z0-9_]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)")

    for root, directories, files in os.walk(directory):
        directories[:] = [d for d in directories if d not in IGNORED_DIRECTORIES]

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in {".cpp", ".cc", ".cxx", ".h", ".hpp", ".c"}:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, directory).replace("\\", "/")
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    found_classes = class_regex.findall(content) + struct_regex.findall(content)
                    found_fns = [m for m in fn_regex_cpp.findall(content) if m not in {"if", "for", "while", "switch"}]
                    extra_classes += len(found_classes)
                    extra_functions += len(found_fns)
                    symbol_files.append({
                        "file": rel_path,
                        "classes": found_classes,
                        "functions": found_fns
                    })
                except OSError:
                    pass
            elif ext in {".js", ".jsx", ".ts", ".tsx"}:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, directory).replace("\\", "/")
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    found_classes = class_regex.findall(content)
                    found_fns = [m[0] or m[1] for m in fn_regex_js.findall(content) if (m[0] or m[1])]
                    extra_classes += len(found_classes)
                    extra_functions += len(found_fns)
                    symbol_files.append({
                        "file": rel_path,
                        "classes": found_classes,
                        "functions": found_fns
                    })
                except OSError:
                    pass

    return {
        "extra_classes": extra_classes,
        "extra_functions": extra_functions,
        "symbol_files": symbol_files
    }


# ---------------------------------------------------------
# Read README
# ---------------------------------------------------------

def read_readme(directory):
    possible_readmes = ["README.md", "README.txt", "readme.md"]

    for readme in possible_readmes:
        path = os.path.join(directory, readme)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8-sig", errors="replace") as file:
                    content = file.read()
                return content[:10000]
            except (UnicodeDecodeError, OSError):
                return ""

    return ""


# ---------------------------------------------------------
# Read Requirements
# ---------------------------------------------------------

def read_requirements(directory):
    path = os.path.join(directory, "requirements.txt")
    if not os.path.exists(path):
        return []

    dependencies = []
    try:
        with open(path, "r", encoding="utf-8-sig") as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith("#"):
                    dependencies.append(line)
    except (UnicodeDecodeError, OSError):
        pass

    return dependencies


# ---------------------------------------------------------
# FR-02: Technology Stack Detection
# ---------------------------------------------------------

def detect_tech_stack(directory, languages, python_analysis):
    """
    FR-02: Detect and display the primary languages, frameworks, libraries,
    and package managers in the repository.
    """
    frameworks = []
    package_managers = []
    build_tools = []
    testing_tools = []
    architecture = "Application"

    imports_set = set(python_analysis.get("imports", []))

    # Python frameworks
    if "fastapi" in imports_set or os.path.exists(os.path.join(directory, "backend", "main.py")):
        frameworks.append("FastAPI")
    if "flask" in imports_set:
        frameworks.append("Flask")
    if "django" in imports_set:
        frameworks.append("Django")
    if "torch" in imports_set or "tensorflow" in imports_set:
        frameworks.append("PyTorch/TensorFlow (ML/AI)")

    # JavaScript/TypeScript frameworks
    pkg_json_path = os.path.join(directory, "package.json")
    if os.path.exists(pkg_json_path):
        try:
            with open(pkg_json_path, "r", encoding="utf-8", errors="ignore") as f:
                pkg_data = json.load(f)
                all_deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}
                if "react" in all_deps or "react-dom" in all_deps:
                    frameworks.append("React")
                if "vue" in all_deps:
                    frameworks.append("Vue")
                if "next" in all_deps:
                    frameworks.append("Next.js")
                if "express" in all_deps:
                    frameworks.append("Express.js")
                if "jest" in all_deps or "vitest" in all_deps:
                    testing_tools.append("Jest/Vitest")
        except Exception:
            pass

    # Package managers & build tools
    if os.path.exists(os.path.join(directory, "requirements.txt")) or os.path.exists(os.path.join(directory, "pyproject.toml")):
        package_managers.append("pip")
    if os.path.exists(os.path.join(directory, "package.json")):
        package_managers.append("npm")
    if os.path.exists(os.path.join(directory, "yarn.lock")):
        package_managers.append("yarn")
    if os.path.exists(os.path.join(directory, "pnpm-lock.yaml")):
        package_managers.append("pnpm")
    if os.path.exists(os.path.join(directory, "Cargo.toml")):
        package_managers.append("Cargo")
    if os.path.exists(os.path.join(directory, "pom.xml")):
        build_tools.append("Maven")
    if os.path.exists(os.path.join(directory, "build.gradle")) or os.path.exists(os.path.join(directory, "build.gradle.kts")):
        build_tools.append("Gradle")
    if os.path.exists(os.path.join(directory, "CMakeLists.txt")):
        build_tools.append("CMake")
    if os.path.exists(os.path.join(directory, "Makefile")):
        build_tools.append("Make")
    if os.path.exists(os.path.join(directory, "Dockerfile")) or os.path.exists(os.path.join(directory, "docker-compose.yml")):
        build_tools.append("Docker")

    # Testing
    test_dir = os.path.join(directory, "tests")
    if os.path.exists(test_dir) or any("test" in f["file"].lower() for f in python_analysis.get("files", [])):
        testing_tools.append("Python unittest / pytest")

    # C++ frameworks / architecture check
    if "C++" in languages or "C" in languages:
        build_tools.append("C++ Compiler (g++ / clang / MSVC)")
        if not frameworks:
            frameworks.append("Standard C++ Library (STL)")

    # Primary language
    sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
    primary_language = sorted_langs[0][0] if sorted_langs else "Unknown"

    return {
        "primary_language": primary_language,
        "languages": [l[0] for l in sorted_langs],
        "frameworks": frameworks or ["Custom / Native Engine"],
        "package_managers": package_managers or ["Standard tooling"],
        "build_tools": build_tools or ["Standard compiler / interpreter"],
        "testing_tools": testing_tools or ["Manual verification"],
        "architecture": architecture
    }


# ---------------------------------------------------------
# FR-03: Interactive Codebase Map Generation
# ---------------------------------------------------------

def generate_codebase_map(directory, languages, python_analysis):
    """
    FR-03: Codebase Structure Explorer / Interactive Codebase Map.
    Parses files, folders, modules, functions, and dependencies into an
    interactive map with entry points, layers, and module relationships.
    """
    modules = []
    entry_points = []
    layers = {
        "Presentation & UI": [],
        "API & Routing": [],
        "Core Logic & Analyzer": [],
        "Data & Storage": [],
        "Testing & QA": [],
        "Configuration & Docs": []
    }

    # Discover top-level and second-level modules/directories
    try:
        top_entries = sorted(os.listdir(directory))
    except OSError:
        top_entries = []

    for entry in top_entries:
        if entry in IGNORED_DIRECTORIES:
            continue
        entry_path = os.path.join(directory, entry)

        if os.path.isdir(entry_path):
            sub_files = []
            sub_langs = set()
            py_classes = 0
            py_functions = 0

            for root, dirs, files in os.walk(entry_path):
                dirs[:] = [d for d in dirs if d not in IGNORED_DIRECTORIES]
                for f in files:
                    rel = os.path.relpath(os.path.join(root, f), directory).replace("\\", "/")
                    sub_files.append(rel)
                    ext = os.path.splitext(f)[1].lower()
                    if ext in LANGUAGE_EXTENSIONS:
                        sub_langs.add(LANGUAGE_EXTENSIONS[ext])

            # Classify layer
            entry_lower = entry.lower()
            if entry_lower in {"frontend", "ui", "views", "templates", "static"}:
                layer = "Presentation & UI"
                desc = "User interface components, HTML/CSS layout, and client-side interactions."
            elif entry_lower in {"backend", "api", "server", "routes", "controllers"}:
                layer = "API & Routing"
                desc = "FastAPI / HTTP endpoints, request handlers, and service orchestrators."
            elif entry_lower in {"analyzer", "core", "engine", "services", "src", "lib"}:
                layer = "Core Logic & Analyzer"
                desc = "Repository parsing, code intelligence, and algorithmic business logic."
            elif entry_lower in {"tests", "test", "spec"}:
                layer = "Testing & QA"
                desc = "Automated test suites, unit validations, and regression safeguards."
            elif entry_lower in {"data", "database", "models", "storage"}:
                layer = "Data & Storage"
                desc = "Repository storage, analysis JSON caches, and persistent assets."
            else:
                layer = "Core Logic & Analyzer"
                desc = f"Domain module providing {entry} functionality."

            # Calculate classes & functions in module
            for pf in python_analysis.get("files", []):
                if pf["file"].startswith(entry + "/"):
                    py_classes += len(pf.get("classes", []))
                    py_functions += len(pf.get("functions", []))

            module_info = {
                "id": entry,
                "name": entry,
                "layer": layer,
                "description": desc,
                "file_count": len(sub_files),
                "languages": sorted(list(sub_langs)),
                "classes": py_classes,
                "functions": py_functions,
                "key_files": sub_files[:5]
            }
            modules.append(module_info)
            layers[layer].append(entry)

    # Detect Root files as a module if files exist at root
    root_files = [f for f in top_entries if os.path.isfile(os.path.join(directory, f)) and not is_sensitive_filename(f)]
    if root_files:
        modules.append({
            "id": "root",
            "name": "Project Root",
            "layer": "Configuration & Docs",
            "description": "Root project definitions, entry points, configuration, and documentation.",
            "file_count": len(root_files),
            "languages": [LANGUAGE_EXTENSIONS.get(os.path.splitext(f)[1].lower(), "Text") for f in root_files if os.path.splitext(f)[1].lower() in LANGUAGE_EXTENSIONS],
            "classes": 0,
            "functions": 0,
            "key_files": root_files[:6]
        })
        layers["Configuration & Docs"].append("Project Root")

    # Detect Entry Points
    entry_candidates = [
        ("main.py", "Primary Python application entry point / runner"),
        ("app.py", "Web application entry point"),
        ("backend/main.py", "FastAPI backend server entry point"),
        ("frontend/index.html", "Web UI entry point"),
        ("main.cpp", "C++ executable main() entry point"),
        ("index.js", "Node.js application bootstrap"),
        ("server.js", "Server bootstrap script"),
    ]

    for candidate, reason in entry_candidates:
        cand_path = os.path.join(directory, candidate)
        if os.path.exists(cand_path):
            entry_points.append({
                "file": candidate.replace("\\", "/"),
                "type": "Application Entry Point",
                "reason": reason
            })

    # Detect graph connections between modules
    connections = []
    if any(m["id"] == "frontend" for m in modules) and any(m["id"] == "backend" for m in modules):
        connections.append({"from": "frontend", "to": "backend", "label": "HTTP API requests"})
    if any(m["id"] == "backend" for m in modules) and any(m["id"] == "analyzer" for m in modules):
        connections.append({"from": "backend", "to": "analyzer", "label": "Invokes analysis & search"})
    if any(m["id"] == "analyzer" for m in modules) and any(m["id"] == "data" for m in modules):
        connections.append({"from": "analyzer", "to": "data", "label": "Reads/writes cloned repos & JSON"})
    if any(m["id"] == "tests" for m in modules):
        if any(m["id"] == "backend" for m in modules):
            connections.append({"from": "tests", "to": "backend", "label": "Validates API endpoints"})
        if any(m["id"] == "analyzer" for m in modules):
            connections.append({"from": "tests", "to": "analyzer", "label": "Validates parsers & loaders"})

    # If single-folder or C++ engine
    if not connections and len(modules) <= 2:
        connections.append({"from": "Project Root", "to": "Core Engine", "label": "Compiles & executes"})

    # Filter empty layers
    active_layers = {k: v for k, v in layers.items() if v}

    return {
        "modules": modules,
        "entry_points": entry_points,
        "layers": active_layers,
        "connections": connections
    }


# ---------------------------------------------------------
# FR-15 & FR-16: Git History (Knowledge & Evolution)
# ---------------------------------------------------------

def analyze_git_history(directory):
    """
    FR-15: Knowledge Concentration (historical contribution & expertise concentration).
    FR-16: Code Evolution Timeline (reconstructs how key modules changed over Git history).
    """
    commits_data = []
    authors_commits = {}
    authors_files = {}
    module_authors = {}

    try:
        from git import Repo
        repo = Repo(directory)
        commits = list(repo.iter_commits(max_count=50))
    except Exception:
        commits = []

    for c in commits:
        author = c.author.name or "Contributor"
        dt_str = c.committed_datetime.strftime("%Y-%m-%d %H:%M")
        msg = c.message.strip().split("\n")[0]
        sha = c.hexsha[:7]

        try:
            files_touched = list(c.stats.files.keys())
        except Exception:
            files_touched = []

        # Tally author commits
        authors_commits[author] = authors_commits.get(author, 0) + 1
        if author not in authors_files:
            authors_files[author] = set()
        for f in files_touched:
            authors_files[author].add(f)

            # Module tracking
            parts = f.replace("\\", "/").split("/")
            mod = parts[0] if len(parts) > 1 else "Root"
            if mod not in module_authors:
                module_authors[mod] = {}
            module_authors[mod][author] = module_authors[mod].get(author, 0) + 1

        # Classify commit change type
        msg_lower = msg.lower()
        if any(msg_lower.startswith(k) for k in ["feat", "add", "implement", "support"]):
            change_type = "Feature"
        elif any(msg_lower.startswith(k) for k in ["fix", "bug", "patch"]):
            change_type = "Bug Fix"
        elif any(msg_lower.startswith(k) for k in ["refactor", "clean"]):
            change_type = "Refactor"
        elif any(msg_lower.startswith(k) for k in ["doc", "readme"]):
            change_type = "Documentation"
        else:
            change_type = "Update"

        commits_data.append({
            "hash": sha,
            "author": author,
            "date": dt_str,
            "message": msg,
            "files_count": len(files_touched),
            "files": files_touched[:5],
            "type": change_type
        })

    total_commits = len(commits_data) or 1

    # Knowledge Concentration breakdown
    author_breakdown = []
    for author, count in authors_commits.items():
        percentage = round((count / total_commits) * 100, 1)
        author_breakdown.append({
            "author": author,
            "commits": count,
            "percentage": percentage,
            "files_touched_count": len(authors_files.get(author, set())),
            "role": "Lead Architect / Code Owner" if percentage >= 50 else "Core Contributor"
        })
    author_breakdown.sort(key=lambda x: x["commits"], reverse=True)

    # Module ownership & bus factor analysis
    module_ownership = []
    high_risk_modules = []

    for mod, auth_counts in module_authors.items():
        mod_total = sum(auth_counts.values())
        top_author = max(auth_counts.items(), key=lambda x: x[1])
        top_pct = round((top_author[1] / mod_total) * 100, 1)

        if top_pct >= 75:
            risk = "High"
            risk_color = "#e5484d"
            high_risk_modules.append(mod)
        elif top_pct >= 50:
            risk = "Medium"
            risk_color = "#f76b15"
        else:
            risk = "Low"
            risk_color = "#46a758"

        module_ownership.append({
            "module": mod,
            "primary_owner": top_author[0],
            "concentration_percentage": top_pct,
            "risk_level": risk,
            "risk_color": risk_color,
            "recommendation": f"Consult {top_author[0]} for architecture decisions on {mod}."
        })

    # If no git commits (e.g. fresh folder or no git), fallback gracefully
    if not author_breakdown:
        author_breakdown = [{
            "author": "Current Codebase Owner",
            "commits": 1,
            "percentage": 100.0,
            "files_touched_count": 1,
            "role": "Initial Author"
        }]
        module_ownership = [{
            "module": "Root",
            "primary_owner": "Current Codebase Owner",
            "concentration_percentage": 100.0,
            "risk_level": "Medium",
            "risk_color": "#f76b15",
            "recommendation": "Review latest commits and documentation."
        }]

    knowledge_concentration = {
        "total_commits_analyzed": len(commits_data),
        "total_contributors": len(author_breakdown),
        "contributors": author_breakdown,
        "module_ownership": module_ownership,
        "high_risk_modules": high_risk_modules,
        "primary_maintainer": author_breakdown[0]["author"] if author_breakdown else "Unknown",
        "bus_factor_alert": (
            f"Knowledge is heavily concentrated ({author_breakdown[0]['percentage']}%) with {author_breakdown[0]['author']}. "
            "Pair programming and documented onboarding are recommended."
            if author_breakdown and author_breakdown[0]["percentage"] > 70
            else "Knowledge is well distributed across multiple contributors."
        )
    }

    code_evolution_timeline = {
        "total_events": len(commits_data),
        "events": commits_data
    }

    return knowledge_concentration, code_evolution_timeline


# ---------------------------------------------------------
# FR-20: Sensitive Files Scan
# ---------------------------------------------------------

def scan_sensitive_files(directory):
    """
    FR-20 & US-SEC-02: Identifies sensitive files (e.g. .env, private keys)
    and ensures they are excluded from AI processing.
    """
    sensitive_found = []

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRECTORIES]
        for f in files:
            if is_sensitive_filename(f):
                rel = os.path.relpath(os.path.join(root, f), directory).replace("\\", "/")
                sensitive_found.append(rel)

    return {
        "sensitive_files_detected": sensitive_found,
        "count": len(sensitive_found),
        "policy": "Protected - excluded from AI search, context, and prompts (FR-20 / US-SEC-02 / DR-03)",
        "status": "Secure" if not sensitive_found else "Protected (Excluded from AI)"
    }


# ---------------------------------------------------------
# Generate Project Information
# ---------------------------------------------------------

def generate_project_info(directory):
    print("\nAnalyzing repository...")

    file_count, directory_count, languages = analyze_repository(directory)
    important_files = find_important_files(directory)
    file_tree = build_file_tree(directory)
    python_analysis = analyze_python_code(directory)
    multi_symbols = analyze_multi_language_symbols(directory)

    # Combine symbols
    total_classes = python_analysis["total_classes"] + multi_symbols["extra_classes"]
    total_functions = python_analysis["total_functions"] + multi_symbols["extra_functions"]

    readme = read_readme(directory)
    requirements = read_requirements(directory)
    project_name = os.path.basename(os.path.abspath(directory))

    # Extended features for Complete Report Phase 1
    tech_stack = detect_tech_stack(directory, languages, python_analysis)
    codebase_map = generate_codebase_map(directory, languages, python_analysis)
    knowledge_concentration, code_evolution_timeline = analyze_git_history(directory)
    security_scan = scan_sensitive_files(directory)

    project_info = {
        "project_name": project_name,
        "statistics": {
            "files": file_count,
            "directories": directory_count,
            "total_classes": total_classes,
            "total_functions": total_functions
        },
        "languages": languages,
        "tech_stack": tech_stack,
        "codebase_map": codebase_map,
        "knowledge_concentration": knowledge_concentration,
        "code_evolution_timeline": code_evolution_timeline,
        "security_scan": security_scan,
        "important_files": important_files,
        "python_analysis": python_analysis,
        "dependencies": {
            "python_requirements": requirements
        },
        "readme": readme,
        "file_tree": file_tree
    }

    return project_info


# ---------------------------------------------------------
# Save JSON
# ---------------------------------------------------------

def save_project_info(project_info, output_path):
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(project_info, file, indent=4)

    print("\nProject information saved!")
    print("Output:", output_path)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

if __name__ == "__main__":
    repository_path = "data/cloned_repo"
    output_path = "data/project_info.json"

    if not os.path.exists(repository_path):
        print("Repository not found.")
        print("Run repository_loader.py first.")
    else:
        project_info = generate_project_info(repository_path)
        save_project_info(project_info, output_path)
        print("\nAnalysis Complete!")
        print("Files:", project_info["statistics"]["files"])
        print("Directories:", project_info["statistics"]["directories"])
        print("Classes:", project_info["statistics"]["total_classes"])
        print("Functions:", project_info["statistics"]["total_functions"])
        print("Dependencies:", len(project_info["dependencies"]["python_requirements"]))