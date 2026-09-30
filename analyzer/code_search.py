import os
import re


# =========================================================
# Directories to Ignore
# =========================================================

IGNORED_DIRECTORIES = {
    ".git",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".env",
    "build",
    "dist",
    ".idea",
    ".vscode",
}


# =========================================================
# File Extensions to Ignore
# =========================================================

IGNORED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".bmp",
    ".webp",

    ".exe",
    ".dll",
    ".so",
    ".dylib",

    ".zip",
    ".rar",
    ".7z",

    ".pdf",

    ".pyc",
    ".class",

    ".obj",
    ".o",

    ".bin",
    ".dat",
}


# =========================================================
# Stop Words
# =========================================================

STOP_WORDS = {
    "what",
    "is",
    "the",
    "a",
    "an",
    "how",
    "does",
    "do",
    "where",
    "why",
    "when",
    "which",
    "who",
    "are",
    "this",
    "that",
    "of",
    "in",
    "on",
    "for",
    "to",
    "and",
    "or",
    "with",
    "from",
    "about",
    "can",
    "it",
    "its",
    "be",
    "used",
    "use",
    "does",
    "tell",
    "me",
    "please",
    "explain",
    "show",
}


# =========================================================
# Extract Keywords
# =========================================================

def extract_keywords(query):
    """
    Extract meaningful keywords from a natural-language question.
    """

    words = re.findall(
        r"[A-Za-z_][A-Za-z0-9_]*",
        query.lower()
    )

    keywords = []

    for word in words:

        if word in STOP_WORDS:
            continue

        if len(word) < 3:
            continue

        if word not in keywords:
            keywords.append(word)

    return keywords


# =========================================================
# Check Whether File Can Be Searched
# =========================================================

def should_search_file(filename):
    """
    Returns True if the file should be searched.
    """

    extension = os.path.splitext(filename)[1].lower()

    return extension not in IGNORED_EXTENSIONS


# =========================================================
# Search Codebase
# =========================================================

def search_codebase(
    directory,
    query,
    max_results=10
):
    """
    Search a repository for code relevant to a question.

    The search uses:
        - exact query matching
        - keyword matching
        - filename matching
        - nearby lines for additional context

    Returns a list of relevant code locations.
    """

    results = []

    # -----------------------------------------------------
    # Validate directory
    # -----------------------------------------------------

    if not os.path.exists(directory):
        return results

    if not os.path.isdir(directory):
        return results

    # -----------------------------------------------------
    # Clean query
    # -----------------------------------------------------

    original_query = query.strip()

    if not original_query:
        return results

    query_lower = original_query.lower()

    # -----------------------------------------------------
    # Extract keywords
    # -----------------------------------------------------

    keywords = extract_keywords(original_query)

    if not keywords:
        return results

    # -----------------------------------------------------
    # Search repository
    # -----------------------------------------------------

    for root, directories, files in os.walk(directory):

        # Ignore unnecessary directories
        directories[:] = [
            directory_name
            for directory_name in directories
            if directory_name not in IGNORED_DIRECTORIES
        ]

        for filename in files:

            if not should_search_file(filename):
                continue

            file_path = os.path.join(
                root,
                filename
            )

            # -------------------------------------------------
            # Read file
            # -------------------------------------------------

            try:

                with open(
                    file_path,
                    "r",
                    encoding="utf-8",
                    errors="ignore"
                ) as file:

                    lines = file.readlines()

            except (
                PermissionError,
                OSError,
            ):

                continue

            if not lines:
                continue

            relative_path = os.path.relpath(
                file_path,
                directory
            )

            relative_path = relative_path.replace(
                "\\",
                "/"
            )

            filename_lower = filename.lower()

            # -------------------------------------------------
            # Search each line
            # -------------------------------------------------

            for line_number, line in enumerate(
                lines,
                start=1
            ):

                line_lower = line.lower()

                score = 0

                # ---------------------------------------------
                # Exact question match
                # ---------------------------------------------

                if query_lower in line_lower:
                    score += 20

                # ---------------------------------------------
                # Keyword matches
                # ---------------------------------------------

                matched_keywords = 0

                for keyword in keywords:

                    if keyword in line_lower:

                        score += 3
                        matched_keywords += 1

                    # Filename match
                    if keyword in filename_lower:

                        score += 2

                # ---------------------------------------------
                # Give bonus when multiple keywords
                # occur in the same line.
                # ---------------------------------------------

                if matched_keywords >= 2:
                    score += 4

                if matched_keywords >= 3:
                    score += 5

                # ---------------------------------------------
                # Skip irrelevant lines
                # ---------------------------------------------

                if score == 0:
                    continue

                # ---------------------------------------------
                # Add result
                # ---------------------------------------------

                results.append({
                    "file": relative_path,
                    "line": line_number,
                    "content": line.strip(),
                    "score": score
                })

    # =========================================================
    # If no exact results, search filenames
    # =========================================================

    if not results:

        for root, directories, files in os.walk(directory):

            directories[:] = [
                directory_name
                for directory_name in directories
                if directory_name not in IGNORED_DIRECTORIES
            ]

            for filename in files:

                if not should_search_file(filename):
                    continue

                filename_lower = filename.lower()

                matched_keywords = [
                    keyword
                    for keyword in keywords
                    if keyword in filename_lower
                ]

                if not matched_keywords:
                    continue

                file_path = os.path.join(
                    root,
                    filename
                )

                try:

                    with open(
                        file_path,
                        "r",
                        encoding="utf-8",
                        errors="ignore"
                    ) as file:

                        lines = file.readlines()

                except (
                    PermissionError,
                    OSError,
                ):

                    continue

                relative_path = os.path.relpath(
                    file_path,
                    directory
                )

                relative_path = relative_path.replace(
                    "\\",
                    "/"
                )

                # Return a few lines from the matching file
                for line_number, line in enumerate(
                    lines[:20],
                    start=1
                ):

                    results.append({
                        "file": relative_path,
                        "line": line_number,
                        "content": line.strip(),
                        "score": len(matched_keywords) * 2
                    })

                    if len(results) >= max_results:
                        break

            if len(results) >= max_results:
                break

    # =========================================================
    # Sort by relevance
    # =========================================================

    results.sort(
        key=lambda result: result["score"],
        reverse=True
    )

    # =========================================================
    # Remove duplicate results
    # =========================================================

    unique_results = []

    seen = set()

    for result in results:

        key = (
            result["file"],
            result["line"]
        )

        if key in seen:
            continue

        seen.add(key)

        unique_results.append(result)

        if len(unique_results) >= max_results:
            break

    return unique_results