import os


# File extensions and their programming languages
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


# Important files that help developers understand a project
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

        # Ignore Git's internal directory
        if ".git" in directories:
            directories.remove(".git")

        # Count directories
        directory_count += len(directories)

        # Analyze files
        for file in files:

            file_count += 1

            # Get file extension
            extension = os.path.splitext(file)[1].lower()

            # Check if extension belongs to a known language
            if extension in LANGUAGE_EXTENSIONS:

                language = LANGUAGE_EXTENSIONS[extension]

                if language not in language_count:
                    language_count[language] = 0

                language_count[language] += 1

    print("Repository:", os.path.basename(os.path.abspath(directory)))
    print("Files:", file_count)
    print("Directories:", directory_count)

    print("\nLanguages / File Types")
    print("----------------------")

    if language_count:

        for language, count in sorted(language_count.items()):
            print(f"{language}: {count} files")

    else:

        print("No recognized programming languages found.")


def print_file_tree(directory, prefix=""):
    """
    Print the repository as a tree structure.
    """

    try:
        entries = sorted(os.listdir(directory))
    except PermissionError:
        return

    # Ignore Git's internal folder
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


def find_important_files(directory):
    """
    Find important files that help developers
    understand the project.
    """

    found_files = []

    for root, directories, files in os.walk(directory):

        # Ignore Git's internal directory
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


if __name__ == "__main__":

    # Location where repository_loader.py
    # downloaded the repository
    repository_path = "data/cloned_repo"

    # Check whether repository exists
    if not os.path.exists(repository_path):

        print("Repository not found.")
        print(
            "Run repository_loader.py first."
        )

    else:

        # 1. Analyze repository
        analyze_repository(
            repository_path
        )

        # 2. Find important files
        find_important_files(
            repository_path
        )

        # 3. Print project structure
        print("\nProject Structure")
        print("=================")

        print_file_tree(
            repository_path
        )