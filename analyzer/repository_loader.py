import os
import shutil
import stat
import tempfile
import time

from git import Repo


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

        os.makedirs(parent_directory, exist_ok=True)
        temporary_directory = tempfile.mkdtemp(
            prefix=".repository-clone-",
            dir=parent_directory
        )

        print("Cloning repository...")

        Repo.clone_from(
            repo_url,
            temporary_directory
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