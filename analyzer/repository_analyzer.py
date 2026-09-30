import os


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


def analyze_repository(directory):
    """Analyze the basic structure of a repository."""

    file_count = 0
    directory_count = 0
    language_count = {}

    print("\nRepository Analysis")
    print("===================")

    for root, directories, files in os.walk(directory):

        directory_count += len(directories)

        for file in files:

            file_count += 1

            extension = os.path.splitext(file)[1].lower()

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
        entry for entry in entries
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
            print(prefix + connector + "📁 " + entry)

            print_file_tree(
                path,
                new_prefix
            )

        else:
            print(prefix + connector + "📄 " + entry)


if __name__ == "__main__":

    repository_path = "data/cloned_repo"

    if not os.path.exists(repository_path):

        print("Repository not found.")
        print("Run repository_loader.py first.")

    else:

        analyze_repository(repository_path)

        print("\nProject Structure")
        print("=================")

        print_file_tree(repository_path)