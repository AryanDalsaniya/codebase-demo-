import os
import ast
import json


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
}


IMPORTANT_FILES = {
    "README.md": "Project documentation",
    "README.txt": "Project documentation",
    "requirements.txt": "Python dependencies",
    "package.json": "Node.js dependencies and scripts",
    "package-lock.json": "Node.js dependency lock file",
    "pom.xml": "Maven configuration",
    "build.gradle": "Gradle build configuration",
    "CMakeLists.txt": "CMake build configuration",
    "Makefile": "Build automation",
    "Dockerfile": "Docker configuration",
    "docker-compose.yml": "Docker Compose configuration",
    "docker-compose.yaml": "Docker Compose configuration",
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
                )

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

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            source_code = file.read()

        tree = ast.parse(source_code)

    except (SyntaxError, UnicodeDecodeError, OSError):

        return classes, functions, imports

    for node in ast.walk(tree):

        if isinstance(node, ast.ClassDef):

            classes.append(node.name)

        elif isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef)
        ):

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
            )

            classes, functions, imports = (
                analyze_python_file(file_path)
            )

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
# Read README
# ---------------------------------------------------------

def read_readme(directory):

    possible_readmes = [
        "README.md",
        "README.txt"
    ]

    for readme in possible_readmes:

        path = os.path.join(
            directory,
            readme
        )

        if os.path.exists(path):

            try:

                with open(
                    path,
                    "r",
                    encoding="utf-8-sig",
                    errors="replace"
                ) as file:

                    content = file.read()

                # Limit size so JSON does not become huge
                return content[:10000]

            except (UnicodeDecodeError, OSError):

                return ""

    return ""


# ---------------------------------------------------------
# Read Requirements
# ---------------------------------------------------------

def read_requirements(directory):

    path = os.path.join(
        directory,
        "requirements.txt"
    )

    if not os.path.exists(path):
        return []

    dependencies = []

    try:

        with open(
            path,
            "r",
            encoding="utf-8-sig"
        ) as file:

            for line in file:

                line = line.strip()

                if line and not line.startswith("#"):

                    dependencies.append(line)

    except (UnicodeDecodeError, OSError):

        pass

    return dependencies


# ---------------------------------------------------------
# Generate Project Information
# ---------------------------------------------------------

def generate_project_info(directory):

    print("\nAnalyzing repository...")

    file_count, directory_count, languages = (
        analyze_repository(directory)
    )

    important_files = find_important_files(
        directory
    )

    file_tree = build_file_tree(
        directory
    )

    python_analysis = analyze_python_code(
        directory
    )

    readme = read_readme(
        directory
    )

    requirements = read_requirements(
        directory
    )

    project_name = os.path.basename(
        os.path.abspath(directory)
    )

    project_info = {

        "project_name": project_name,

        "statistics": {
            "files": file_count,
            "directories": directory_count
        },

        "languages": languages,

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

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            project_info,
            file,
            indent=4
        )

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

        print(
            "Run repository_loader.py first."
        )

    else:

        project_info = generate_project_info(
            repository_path
        )

        save_project_info(
            project_info,
            output_path
        )

        print("\nAnalysis Complete!")
        print(
            "Files:",
            project_info["statistics"]["files"]
        )

        print(
            "Directories:",
            project_info["statistics"]["directories"]
        )

        print(
            "Classes:",
            project_info["python_analysis"]["total_classes"]
        )

        print(
            "Functions:",
            project_info["python_analysis"]["total_functions"]
        )

        print(
            "Dependencies:",
            len(
                project_info["dependencies"][
                    "python_requirements"
                ]
            )
        )