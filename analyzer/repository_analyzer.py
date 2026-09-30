import os
import ast


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


# ---------------------------------------------------------
# Important Project Files
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Basic Repository Analysis
# ---------------------------------------------------------

def analyze_repository(directory):
    """
    Analyze the basic structure of a repository.
    """

    file_count = 0
    directory_count = 0
    language_count = {}

    print("\nRepository Analysis")
    print("===================")

    for root, directories, files in os.walk(directory):

        # Ignore Git internal directory
        if ".git" in directories:
            directories.remove(".git")

        directory_count += len(directories)

        for file in files:

            file_count += 1

            extension = os.path.splitext(file)[1].lower()

            if extension in LANGUAGE_EXTENSIONS:

                language = LANGUAGE_EXTENSIONS[extension]

                if language not in language_count:
                    language_count[language] = 0

                language_count[language] += 1

    print(
        "Repository:",
        os.path.basename(os.path.abspath(directory))
    )

    print("Files:", file_count)
    print("Directories:", directory_count)

    print("\nLanguages / File Types")
    print("----------------------")

    if language_count:

        for language, count in sorted(language_count.items()):
            print(f"{language}: {count} files")

    else:

        print("No recognized programming languages found.")


# ---------------------------------------------------------
# Project File Tree
# ---------------------------------------------------------

def print_file_tree(directory, prefix=""):
    """
    Print the repository as a tree structure.
    """

    try:
        entries = sorted(os.listdir(directory))
    except PermissionError:
        return

    entries = [
        entry
        for entry in entries
        if entry != ".git"
    ]

    for index, entry in enumerate(entries):

        path = os.path.join(directory, entry)

        is_last = index == len(entries) - 1

        if is_last:

            connector = "└── "
            new_prefix = prefix + "    "

        else:

            connector = "├── "
            new_prefix = prefix + "│   "

        if os.path.isdir(path):

            print(
                prefix + connector + "📁 " + entry
            )

            print_file_tree(
                path,
                new_prefix
            )

        else:

            print(
                prefix + connector + "📄 " + entry
            )


# ---------------------------------------------------------
# Important Files
# ---------------------------------------------------------

def find_important_files(directory):
    """
    Find important files that help developers
    understand the project.
    """

    found_files = []

    for root, directories, files in os.walk(directory):

        if ".git" in directories:
            directories.remove(".git")

        for file in files:

            if file in IMPORTANT_FILES:

                full_path = os.path.join(
                    root,
                    file
                )

                relative_path = os.path.relpath(
                    full_path,
                    directory
                )

                description = IMPORTANT_FILES[file]

                found_files.append(
                    (relative_path, description)
                )

    print("\nImportant Project Files")
    print("======================")

    if found_files:

        for path, description in found_files:

            print(
                f"{path} → {description}"
            )

    else:

        print(
            "No important project files detected."
        )


# ---------------------------------------------------------
# Python Source Code Analysis
# ---------------------------------------------------------

def analyze_python_file(file_path):
    """
    Analyze one Python file using AST.

    Returns:
        classes
        functions
        imports
    """

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

        # Find classes
        if isinstance(node, ast.ClassDef):

            classes.append(node.name)

        # Find functions
        elif isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef)
        ):

            functions.append(node.name)

        # Find imports
        elif isinstance(node, ast.Import):

            for alias in node.names:

                imports.append(alias.name)

        # Find "from x import y"
        elif isinstance(node, ast.ImportFrom):

            if node.module:

                imports.append(node.module)

    return classes, functions, imports


# ---------------------------------------------------------
# Analyze All Python Files
# ---------------------------------------------------------

def analyze_python_code(directory):
    """
    Analyze all Python files in the repository.
    """

    total_classes = 0
    total_functions = 0
    all_imports = set()

    print("\nPython Code Analysis")
    print("====================")

    found_python_file = False

    for root, directories, files in os.walk(directory):

        if ".git" in directories:
            directories.remove(".git")

        for file in files:

            if not file.endswith(".py"):
                continue

            found_python_file = True

            file_path = os.path.join(
                root,
                file
            )

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

            print(f"\n📄 {relative_path}")

            if classes:

                print("  Classes:")

                for class_name in classes:
                    print(f"    - {class_name}")

            if functions:

                print("  Functions:")

                for function_name in functions:
                    print(f"    - {function_name}")

            if imports:

                print("  Imports:")

                for imported_module in imports:
                    print(f"    - {imported_module}")

            if not classes and not functions and not imports:

                print("  No classes, functions or imports found.")

    if not found_python_file:

        print("No Python files found.")

        return

    print("\nPython Code Summary")
    print("-------------------")

    print("Total Classes:", total_classes)
    print("Total Functions:", total_functions)

    print("\nAll Imported Modules")
    print("--------------------")

    for imported_module in sorted(all_imports):

        print("-", imported_module)


# ---------------------------------------------------------
# Main Program
# ---------------------------------------------------------

if __name__ == "__main__":

    repository_path = "data/cloned_repo"

    if not os.path.exists(repository_path):

        print("Repository not found.")

        print(
            "Run repository_loader.py first."
        )

    else:

        # 1. Basic repository analysis
        analyze_repository(
            repository_path
        )

        # 2. Important files
        find_important_files(
            repository_path
        )

        # 3. Project structure
        print("\nProject Structure")
        print("=================")

        print_file_tree(
            repository_path
        )

        # 4. Python code analysis
        analyze_python_code(
            repository_path
        )