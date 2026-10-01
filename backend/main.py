from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import os
import json
import logging
import re
import secrets

from analyzer.repository_loader import clone_repository
from analyzer.repository_analyzer import generate_project_info
from analyzer.repository_analyzer import save_project_info
from analyzer.code_search import search_codebase

from backend.llm_service import generate_onboarding_guide
from backend.qa_service import generate_codebase_answer


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIRECTORY = os.path.join(PROJECT_ROOT, "data")
SESSIONS_DIRECTORY = os.path.join(DATA_DIRECTORY, "sessions")
FRONTEND_DIRECTORY = os.path.join(PROJECT_ROOT, "frontend")
logger = logging.getLogger(__name__)


# =========================================================
# FastAPI Application
# =========================================================

app = FastAPI(
    title="Codebase Onboarding Companion",
    description="AI-powered tool for understanding unfamiliar codebases",
    version="1.0"
)


@app.middleware("http")
async def require_app_password(request, call_next):
    app_password = os.environ.get("APP_PASSWORD", "")
    public_paths = {"/", "/script.js", "/style.css", "/healthz"}

    if (
        app_password
        and request.method != "OPTIONS"
        and request.url.path not in public_paths
        and not secrets.compare_digest(
            request.headers.get("X-App-Password", ""),
            app_password,
        )
    ):
        return JSONResponse(
            status_code=401,
            content={"detail": "Enter the app access password to continue."},
        )

    return await call_next(request)


# =========================================================
# CORS Configuration
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.environ.get(
            "CORS_ORIGINS",
            "http://127.0.0.1:5500,http://localhost:5500",
        ).split(",")
        if origin.strip()
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# Request Models
# =========================================================

class RepositoryRequest(BaseModel):
    repo_url: str = Field(min_length=1, max_length=2048)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


def get_session_paths(
    x_session_id: str = Header(alias="X-Session-ID"),
):
    if not re.fullmatch(r"[0-9a-f]{32}", x_session_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid browser session. Refresh the page and try again.",
        )

    session_directory = os.path.join(SESSIONS_DIRECTORY, x_session_id)
    return (
        os.path.join(session_directory, "cloned_repo"),
        os.path.join(session_directory, "project_info.json"),
    )


# =========================================================
# Home
# =========================================================

@app.get("/")
def home():
    return FileResponse(os.path.join(FRONTEND_DIRECTORY, "index.html"))


@app.get("/healthz")
def health_check():
    return {"status": "ok"}


# =========================================================
# Analyze Repository
# =========================================================

@app.post("/analyze")
def analyze_repository(
    request: RepositoryRequest,
    paths: tuple[str, str] = Depends(get_session_paths),
):
    repository_path, project_info_path = paths
    repo_url = request.repo_url.strip()
    if not repo_url:
        raise HTTPException(
            status_code=422,
            detail="Please enter a GitHub repository URL."
        )

    logger.info("Cloning repository from %s", repo_url)
    try:
        clone_success = clone_repository(
            repo_url,
            repository_path,
            raise_errors=True
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        logger.exception("Repository clone failed")
        raise HTTPException(
            status_code=502,
            detail=(
                "Could not clone that repository. Check that the URL is correct, "
                "the repository is public, and GitHub is reachable."
            )
        ) from error

    if not clone_success:
        raise HTTPException(
            status_code=502,
            detail="Could not clone that repository. Check that it is public and reachable."
        )

    try:
        logger.info("Analyzing repository at %s", repository_path)
        project_info = generate_project_info(repository_path)
        os.makedirs(os.path.dirname(project_info_path), exist_ok=True)
        save_project_info(project_info, project_info_path)
    except Exception as error:
        logger.exception("Repository analysis failed")
        raise HTTPException(
            status_code=500,
            detail="The repository was cloned, but its files could not be analyzed."
        ) from error

    logger.info("Repository analysis completed")
    return {
        "success": True,
        "message": "Repository analyzed successfully."
    }


# =========================================================
# Repository Summary
# =========================================================

@app.get("/summary")
def get_summary(paths: tuple[str, str] = Depends(get_session_paths)):
    _, project_info_path = paths

    if not os.path.exists(project_info_path):

        return {
            "success": False,
            "message": "No repository has been analyzed yet."
        }

    try:

        with open(
            project_info_path,
            "r",
            encoding="utf-8-sig"
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
            "dependencies": project_info["dependencies"],
            "readme": project_info.get("readme", "")
        }

    except Exception as e:

        print("ERROR:", repr(e))

        return {
            "success": False,
            "message": "Could not read project information.",
            "error": str(e)
        }


@app.get("/file-tree")
def get_file_tree(paths: tuple[str, str] = Depends(get_session_paths)):
    _, project_info_path = paths

    if not os.path.exists(project_info_path):

        return {
            "success": False,
            "message": "Please analyze a repository first."
        }

    try:

        with open(
            project_info_path,
            "r",
            encoding="utf-8-sig"
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
def get_repository_file(
    path: str,
    paths: tuple[str, str] = Depends(get_session_paths),
):
    repository_path, _ = paths

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

    repository_root = os.path.realpath(repository_path)
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
# AI Onboarding Guide
# =========================================================

@app.get("/onboarding-guide")
def onboarding_guide(paths: tuple[str, str] = Depends(get_session_paths)):
    _, project_info_path = paths

    if not os.path.exists(project_info_path):

        return {
            "success": False,
            "message": "Please analyze a repository first."
        }

    try:

        with open(
            project_info_path,
            "r",
            encoding="utf-8-sig"
        ) as file:

            project_info = json.load(file)

        logger.info("Generating AI onboarding guide")

        guide = generate_onboarding_guide(
            project_info
        )

        logger.info("AI onboarding guide generated")

        return {
            "success": True,
            "guide": guide
        }

    except RuntimeError as error:
        logger.error("AI guide could not be generated: %s", error)
        status_code = 503 if "OPENAI_API_KEY" in str(error) else 502
        raise HTTPException(status_code=status_code, detail=str(error)) from error
    except Exception as error:
        logger.exception("AI guide generation failed")
        raise HTTPException(
            status_code=502,
            detail="The AI provider could not generate an onboarding guide.",
        ) from error


# =========================================================
# Search Codebase
# =========================================================

@app.get("/search")
def search_repository(
    query: str,
    paths: tuple[str, str] = Depends(get_session_paths),
):
    repository_path, _ = paths

    if not os.path.exists(repository_path):

        return {
            "success": False,
            "message": "Please analyze a repository first."
        }

    try:

        print(
            f"Searching repository for: {query}"
        )

        results = search_codebase(
            repository_path,
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
# Codebase Q&A
# =========================================================

@app.post("/ask")
def ask_question(
    request: QuestionRequest,
    paths: tuple[str, str] = Depends(get_session_paths),
):
    repository_path, _ = paths

    if not os.path.exists(repository_path):

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
            repository_path,
            question,
            max_results=10
        )

        print(
            f"Found {len(search_results)} relevant results."
        )


        # -------------------------------------------------
        # Step 2: Send relevant code to the AI provider
        # -------------------------------------------------

        print(
            "Generating answer using OpenAI..."
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

    except RuntimeError as error:
        logger.error("AI answer could not be generated: %s", error)
        status_code = 503 if "OPENAI_API_KEY" in str(error) else 502
        raise HTTPException(status_code=status_code, detail=str(error)) from error
    except Exception as error:
        logger.exception("Codebase answer generation failed")
        raise HTTPException(
            status_code=502,
            detail="The AI provider could not answer this question.",
        ) from error


# Serve the frontend from the same origin in production.
app.mount("/", StaticFiles(directory=FRONTEND_DIRECTORY, html=True), name="frontend")


# =========================================================
# Run Server
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
        reload=True
    )