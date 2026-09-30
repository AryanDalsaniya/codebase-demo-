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


if __name__ == "__main__":

    repository_path = "data/cloned_repo"

    if not os.path.exists(repository_path):

        print("Repository not found.")
        print("Run repository_loader.py first.")

    else:

        analyze_repository(repository_path)