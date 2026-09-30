import os
import shutil
from git import Repo


def clone_repository(repo_url, destination):
    """
    Clone a GitHub repository into the destination folder.
    """

    # If the destination already exists, remove it
    if os.path.exists(destination):
        shutil.rmtree(destination)

    print("Cloning repository...")

    try:
        Repo.clone_from(repo_url, destination)
        print("Repository cloned successfully!")

    except Exception as e:
        print("Failed to clone repository.")
        print("Error:", e)


def analyze_basic_structure(directory):
    """
    Count files and directories in the repository.
    """

    file_count = 0
    directory_count = 0

    for root, directories, files in os.walk(directory):
        directory_count += len(directories)
        file_count += len(files)

    print("\nRepository Information")
    print("----------------------")
    print("Location:", directory)
    print("Files:", file_count)
    print("Directories:", directory_count)


if __name__ == "__main__":

    repo_url = input("Enter GitHub repository URL: ")

    destination = "data/cloned_repo"

    clone_repository(repo_url, destination)

    if os.path.exists(destination):
        analyze_basic_structure(destination)