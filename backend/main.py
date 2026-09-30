from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import os
import json

from analyzer.repository_loader import clone_repository
from analyzer.repository_analyzer import generate_project_info
from analyzer.repository_analyzer import save_project_info
from analyzer.code_search import search_codebase

from backend.llm_service import generate_onboarding_guide
from backend.qa_service import generate_codebase_answer


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIRECTORY = os.path.join(PROJECT_ROOT, "data")
REPOSITORY_PATH = os.path.join(DATA_DIRECTORY, "cloned_repo")
PROJECT_INFO_PATH = os.path.join(DATA_DIRECTORY, "project_info.json")


# =========================================================
# FastAPI Application
# =========================================================

app = FastAPI(
    title="Codebase Onboarding Companion",
    description="AI-powered tool for understanding unfamiliar codebases",
    version="1.0"
)


# =========================================================
# CORS Configuration
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# Request Models
# =========================================================

class RepositoryRequest(BaseModel):
    repo_url: str


class QuestionRequest(BaseModel):
    question: str


# =========================================================
# Home
# =========================================================

@app.get("/")
def home():

    return {
        "message": "Codebase Onboarding Companion API",
        "status": "running"
    }


# =========================================================
# Analyze Repository
# =========================================================

@app.post("/analyze")
def analyze_repository(request: RepositoryRequest):

    try:

        print("Cloning repository...")

        clone_success = clone_repository(
            request.repo_url,
            REPOSITORY_PATH,
            raise_errors=True
        )

        if not clone_success:

            return {
                "success": False,
                "message": "Repository could not be cloned."
            }

        print("Analyzing repository...")

        project_info = generate_project_info(
            REPOSITORY_PATH
        )

        save_project_info(
            project_info,
            PROJECT_INFO_PATH
        )

        print("Repository analysis completed.")

        return {
            "success": True,
            "message": "Repository analyzed successfully."
        }

    except Exception as e:

        print("ERROR:", repr(e))

        return {
            "success": False,
            "message": "An error occurred while analyzing the repository.",
            "error": str(e)
        }


# =========================================================
# Repository Summary
# =========================================================

@app.get("/summary")
def get_summary():

    if not os.path.exists(PROJECT_INFO_PATH):

        return {
            "success": False,
            "message": "No repository has been analyzed yet."
        }

    try:

        with open(
            PROJECT_INFO_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            project_info = json.load(file)

        return {
            "success": True,
            "project_name": project_info["project_name"],
            "statistics": project_info["statistics"],
            "languages": project_info["languages"],
            "important_files": project_info["important_files"],
            "classes": project_info["python_analysis"]["total_classes"],
            "functions": project_info["python_analysis"]["total_functions"],
            "dependencies": project_info["dependencies"]
        }

    except Exception as e:

        print("ERROR:", repr(e))

        return {
            "success": False,
            "message": "Could not read project information.",
            "error": str(e)
        }


@app.get("/file-tree")
def get_file_tree():

    if not os.path.exists(PROJECT_INFO_PATH):

        return {
            "success": False,
            "message": "Please analyze a repository first."
        }

    try:

        with open(
            PROJECT_INFO_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            project_info = json.load(file)

        return {
            "success": True,
            "file_tree": project_info.get("file_tree", [])
        }

    except Exception as e:

        return {
            "success": False,
            "message": "Could not read the repository file tree.",
            "error": str(e)
        }


@app.get("/file")
def get_repository_file(path: str):

    normalized_path = path.strip().replace("\\", "/")
    path_parts = normalized_path.split("/")

    if (
        not normalized_path
        or os.path.isabs(path)
        or os.path.splitdrive(path)[0]
        or any(part in {"", ".", ".."} for part in path_parts)
        or any(part.lower() == ".git" for part in path_parts)
    ):

        return {
            "success": False,
            "message": "Invalid repository file path."
        }

    repository_root = os.path.realpath(REPOSITORY_PATH)
    file_path = os.path.realpath(
        os.path.join(repository_root, *path_parts)
    )

    try:
        if os.path.commonpath((repository_root, file_path)) != repository_root:
            return {
                "success": False,
                "message": "File path is outside the repository."
            }
    except ValueError:
        return {
            "success": False,
            "message": "Invalid repository file path."
        }

    if not os.path.isfile(file_path):

        return {
            "success": False,
            "message": "File not found in the analyzed repository."
        }

    try:

        with open(file_path, "rb") as file:
            content = file.read(1_000_001)

        if len(content) > 1_000_000:
            return {
                "success": False,
                "message": "This file is too large to preview."
            }

        if b"\0" in content:
            return {
                "success": False,
                "message": "Binary files cannot be previewed."
            }

        return {
            "success": True,
            "path": normalized_path,
            "content": content.decode("utf-8", errors="replace")
        }

    except OSError as e:

        return {
            "success": False,
            "message": "Could not read this repository file.",
            "error": str(e)
        }


# =========================================================
# AI Onboarding Guide - Llama 3.2
# =========================================================

@app.get("/onboarding-guide")
def onboarding_guide():

    if not os.path.exists(PROJECT_INFO_PATH):

        return {
            "success": False,
            "message": "Please analyze a repository first."
        }

    try:

        with open(
            PROJECT_INFO_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            project_info = json.load(file)

        print("Generating AI onboarding guide...")

        guide = generate_onboarding_guide(
            project_info
        )

        print("AI onboarding guide generated.")

        return {
            "success": True,
            "guide": guide
        }

    except Exception as e:

        print("ERROR:", repr(e))

        return {
            "success": False,
            "message": "Could not generate onboarding guide.",
            "error": str(e)
        }


# =========================================================
# Search Codebase
# =========================================================

@app.get("/search")
def search_repository(query: str):

    if not os.path.exists(REPOSITORY_PATH):

        return {
            "success": False,
            "message": "Please analyze a repository first."
        }

    try:

        print(
            f"Searching repository for: {query}"
        )

        results = search_codebase(
            REPOSITORY_PATH,
            query
        )

        return {
            "success": True,
            "query": query,
            "results": results
        }

    except Exception as e:

        print("ERROR:", repr(e))

        return {
            "success": False,
            "message": "Could not search repository.",
            "error": str(e)
        }


# =========================================================
# Codebase Q&A - Llama 3.2
# =========================================================

@app.post("/ask")
def ask_question(request: QuestionRequest):

    if not os.path.exists(REPOSITORY_PATH):

        return {
            "success": False,
            "message": "Please analyze a repository first."
        }

    question = request.question.strip()

    if not question:

        return {
            "success": False,
            "message": "Please enter a question."
        }

    try:

        # -------------------------------------------------
        # Step 1: Search repository
        # -------------------------------------------------

        print("Searching codebase...")

        search_results = search_codebase(
            REPOSITORY_PATH,
            question,
            max_results=10
        )

        print(
            f"Found {len(search_results)} relevant results."
        )


        # -------------------------------------------------
        # Step 2: Send relevant code to Llama
        # -------------------------------------------------

        print(
            "Generating answer using Llama 3.2..."
        )

        answer = generate_codebase_answer(
            question,
            search_results
        )

        print("Answer generated.")


        # -------------------------------------------------
        # Step 3: Prepare source references
        # -------------------------------------------------

        sources = []

        for result in search_results:

            sources.append({
                "file": result["file"],
                "line": result["line"]
            })


        # -------------------------------------------------
        # Step 4: Return answer
        # -------------------------------------------------

        return {
            "success": True,
            "question": question,
            "answer": answer,
            "sources": sources
        }

    except Exception as e:

        print("ERROR:", repr(e))

        return {
            "success": False,
            "message": "Could not answer the question.",
            "error": str(e)
        }


# =========================================================
# Run Server
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )