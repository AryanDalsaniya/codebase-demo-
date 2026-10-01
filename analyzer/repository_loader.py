import os
import re
import shutil
import stat
import tempfile
import time
from urllib.parse import unquote, urlsplit

from git import Repo


# =========================================================
# Normalize GitHub Repository URLs
# =========================================================

def normalize_repository_url(repo_url):
    """Return a clone URL for a public GitHub repository URL."""

    value = repo_url.strip()

    if value.startswith("git@github.com:"):
        value = "https://github.com/" + value[len("git@github.com:"):]
    elif value.startswith("github.com/"):
        value = "https://" + value

    parsed = urlsplit(value)

    if (
        parsed.scheme.lower() != "https"
        or parsed.hostname is None
        or parsed.hostname.lower() not in {"github.com", "www.github.com"}
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ValueError(
            "Enter a public GitHub repository URL, such as "
            "https://github.com/owner/repository."
        )

    path_parts = [
        unquote(part)
        for part in parsed.path.strip("/").split("/")
        if part
    ]

    if len(path_parts) < 2:
        raise ValueError(
            "The GitHub URL must include both an owner and a repository name."
        )

    owner, repository = path_parts[:2]

    if repository.lower().endswith(".git"):
        repository = repository[:-4]

    valid_name_pattern = re.compile(r"[A-Za-z0-9_.-]+")
    if (
        owner in {".", ".."}
        or repository in {".", ".."}
        or not valid_name_pattern.fullmatch(owner)
        or not valid_name_pattern.fullmatch(repository)
    ):
        raise ValueError("The GitHub URL contains an invalid owner or repository name.")

    return f"https://github.com/{owner}/{repository}.git"


# =========================================================
# Remove Read-Only Files
# =========================================================

def remove_readonly(func, path, exc_info):
    """
    Handles Windows permission errors when deleting files.
    """

    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)

    except Exception:
        pass


# =========================================================
# Delete Directory Safely
# =========================================================

def delete_directory(directory):
    """
    Safely delete a directory, including Git files
    that may be read-only on Windows.
    """

    if not os.path.exists(directory):
        return

    print("Removing previous repository...")

    try:

        shutil.rmtree(
            directory,
            onerror=remove_readonly
        )

    except Exception as e:

        print("First delete attempt failed:", e)

        # Wait a little in case Windows is releasing a file
        time.sleep(1)

        try:

            shutil.rmtree(
                directory,
                onerror=remove_readonly
            )

        except Exception as e:

            print("Could not delete repository:", e)

            raise


# =========================================================
# Clone Repository
# =========================================================

def clone_repository(repo_url, destination, *, raise_errors=False):
    """
    Clone a GitHub repository into the destination folder.

    Returns:
        True  -> cloning successful
        False -> cloning failed
    """

    destination = os.path.abspath(destination)
    parent_directory = os.path.dirname(destination)
    temporary_directory = None

    try:
        repo_url = normalize_repository_url(repo_url)

        os.makedirs(parent_directory, exist_ok=True)
        temporary_directory = tempfile.mkdtemp(
            prefix=".repository-clone-",
            dir=parent_directory
        )

        print("Cloning repository...")

        Repo.clone_from(
            repo_url,
            temporary_directory,
            multi_options=["--depth=1", "--single-branch"]
        )

        if os.path.exists(destination):
            delete_directory(destination)

        os.replace(temporary_directory, destination)
        temporary_directory = None

        print("Repository cloned successfully!")
        return True

    except Exception as e:

        print("Failed to clone repository.")
        print("Error:", repr(e))

        if raise_errors:
            raise

        return False

    finally:
        if temporary_directory and os.path.exists(temporary_directory):
            try:
                delete_directory(temporary_directory)
            except OSError as e:
                print("Could not remove temporary clone:", e)


# =========================================================
# Basic Repository Analysis
# =========================================================

def analyze_basic_structure(directory):
    """
    Count files and directories in the repository.
    """

    file_count = 0
    directory_count = 0


    for root, directories, files in os.walk(directory):

        # Ignore .git directory
        if ".git" in directories:
            directories.remove(".git")

        directory_count += len(directories)
        file_count += len(files)


    print("\nRepository Information")
    print("----------------------")
    print("Location:", directory)
    print("Files:", file_count)
    print("Directories:", directory_count)


# =========================================================
# Test the Repository Loader
# =========================================================

if __name__ == "__main__":

    repo_url = input(
        "Enter GitHub repository URL: "
    )

    destination = "data/cloned_repo"


    success = clone_repository(
        repo_url,
        destination
    )


    if success:

        analyze_basic_structure(
            destination
        )

    else:

        print(
            "Repository cloning failed."
        )