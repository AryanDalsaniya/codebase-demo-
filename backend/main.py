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
from typing import Optional, List

from analyzer.repository_loader import clone_repository
from analyzer.repository_analyzer import generate_project_info, save_project_info
from analyzer.code_search import search_codebase
from analyzer.impact_analyzer import analyze_change_impact
from analyzer.task_guidance import generate_task_guidance

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
    description="AI-powered tool for understanding unfamiliar codebases (Phase 1)",
    version="1.0"
)


@app.middleware("http")
async def require_app_password(request, call_next):
    app_password = os.environ.get("APP_PASSWORD", "")
    public_paths = {"/", "/script.js", "/style.css", "/healthz", "/health"}

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
            "http://127.0.0.1:5500,http://localhost:5500,*",
        ).split(",")
        if origin.strip()
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# Session Paths Dependency
# =========================================================

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
# Request Models
# =========================================================

class RepositoryRequest(BaseModel):
    repo_url: str = Field(min_length=1, max_length=2048)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    conversation_history: Optional[List[dict]] = Field(default_factory=list)


class ChangePreviewRequest(BaseModel):
    file_path: str
    symbol: Optional[str] = None


class TaskGuidanceRequest(BaseModel):
    task: str


class SeniorReviewRequest(BaseModel):
    approved: bool = True
    feedback: str = ""
    approved_by: str = "Senior Codebase Owner"


# =========================================================
# Health & Status
# =========================================================

@app.get("/")
def home():
    index_path = os.path.join(FRONTEND_DIRECTORY, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "message": "Codebase Onboarding Companion API",
        "status": "running"
    }


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Codebase Onboarding Companion",
        "version": "1.0"
    }


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

    logger.info("Cloning repository from %s into %s", repo_url, repository_path)
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
        with open(project_info_path, "r", encoding="utf-8-sig") as file:
            project_info = json.load(file)

        python_analysis = project_info.get("python_analysis", {})
        classes = python_analysis.get("total_classes", project_info.get("classes", 0))
        functions = python_analysis.get("total_functions", project_info.get("functions", 0))

        return {
            "success": True,
            "project_name": project_info["project_name"],
            "statistics": project_info["statistics"],
            "languages": project_info["languages"],
            "tech_stack": project_info.get("tech_stack", {}),
            "codebase_map": project_info.get("codebase_map", {}),
            "knowledge_concentration": project_info.get("knowledge_concentration", {}),
            "code_evolution_timeline": project_info.get("code_evolution_timeline", {}),
            "security_scan": project_info.get("security_scan", {}),
            "important_files": project_info.get("important_files", []),
            "classes": classes,
            "functions": functions,
            "dependencies": project_info.get("dependencies", {}),
            "readme": project_info.get("readme", "")
        }

    except Exception as e:
        logger.exception("Could not read project info")
        return {
            "success": False,
            "message": "Could not read project information.",
            "error": str(e)
        }


# =========================================================
# FR-02: Technology Stack Detection
# =========================================================

@app.get("/tech-stack")
def get_tech_stack(paths: tuple[str, str] = Depends(get_session_paths)):
    _, project_info_path = paths
    if not os.path.exists(project_info_path):
        return {"success": False, "message": "Please analyze a repository first."}

    try:
        with open(project_info_path, "r", encoding="utf-8-sig") as file:
            project_info = json.load(file)
        return {
            "success": True,
            "tech_stack": project_info.get("tech_stack", {})
        }
    except Exception as e:
        return {"success": False, "message": "Could not read technology stack.", "error": str(e)}


# =========================================================
# FR-03: Codebase Structure Explorer / Codebase Map
# =========================================================

@app.get("/codebase-map")
def get_codebase_map(paths: tuple[str, str] = Depends(get_session_paths)):
    _, project_info_path = paths
    if not os.path.exists(project_info_path):
        return {"success": False, "message": "Please analyze a repository first."}

    try:
        with open(project_info_path, "r", encoding="utf-8-sig") as file:
            project_info = json.load(file)
        return {
            "success": True,
            "codebase_map": project_info.get("codebase_map", {})
        }
    except Exception as e:
        return {"success": False, "message": "Could not read codebase map.", "error": str(e)}


# =========================================================
# FR-15: Knowledge Concentration
# =========================================================

@app.get("/knowledge-concentration")
def get_knowledge_concentration(paths: tuple[str, str] = Depends(get_session_paths)):
    _, project_info_path = paths
    if not os.path.exists(project_info_path):
        return {"success": False, "message": "Please analyze a repository first."}

    try:
        with open(project_info_path, "r", encoding="utf-8-sig") as file:
            project_info = json.load(file)
        return {
            "success": True,
            "knowledge_concentration": project_info.get("knowledge_concentration", {})
        }
    except Exception as e:
        return {"success": False, "message": "Could not read knowledge concentration.", "error": str(e)}


# =========================================================
# FR-16: Code Evolution Timeline
# =========================================================

@app.get("/code-evolution-timeline")
def get_code_evolution_timeline(
    module: Optional[str] = None,
    paths: tuple[str, str] = Depends(get_session_paths)
):
    _, project_info_path = paths
    if not os.path.exists(project_info_path):
        return {"success": False, "message": "Please analyze a repository first."}

    try:
        with open(project_info_path, "r", encoding="utf-8-sig") as file:
            project_info = json.load(file)
        timeline = project_info.get("code_evolution_timeline", {})
        events = timeline.get("events", [])
        if module:
            events = [
                e for e in events
                if any(module.lower() in f.lower() for f in e.get("files", []))
            ]
        return {
            "success": True,
            "total_events": len(events),
            "events": events
        }
    except Exception as e:
        return {"success": False, "message": "Could not read code evolution timeline.", "error": str(e)}


# =========================================================
# FR-14: Change Preview / Impact Awareness
# =========================================================

@app.post("/change-preview")
def change_preview(
    request: ChangePreviewRequest,
    paths: tuple[str, str] = Depends(get_session_paths)
):
    repository_path, _ = paths
    if not os.path.exists(repository_path):
        return {"success": False, "message": "Please analyze a repository first."}

    try:
        impact = analyze_change_impact(
            repository_path,
            request.file_path,
            request.symbol
        )
        return {"success": True, **impact}
    except Exception as e:
        logger.exception("Change preview failed")
        return {"success": False, "message": "Could not calculate change impact preview.", "error": str(e)}


# =========================================================
# FR-13: Task-to-Code Guidance
# =========================================================

@app.post("/task-guidance")
def task_guidance(
    request: TaskGuidanceRequest,
    paths: tuple[str, str] = Depends(get_session_paths)
):
    repository_path, project_info_path = paths
    if not os.path.exists(repository_path) or not os.path.exists(project_info_path):
        return {"success": False, "message": "Please analyze a repository first."}

    try:
        with open(project_info_path, "r", encoding="utf-8-sig") as file:
            project_info = json.load(file)
        guidance = generate_task_guidance(repository_path, project_info, request.task)
        return guidance
    except Exception as e:
        logger.exception("Task guidance failed")
        return {"success": False, "message": "Could not generate task guidance.", "error": str(e)}


# =========================================================
# File Tree & Viewer
# =========================================================

@app.get("/file-tree")
def get_file_tree(paths: tuple[str, str] = Depends(get_session_paths)):
    _, project_info_path = paths
    if not os.path.exists(project_info_path):
        return {
            "success": False,
            "message": "Please analyze a repository first."
        }

    try:
        with open(project_info_path, "r", encoding="utf-8-sig") as file:
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
    file_path = os.path.realpath(os.path.join(repository_root, *path_parts))

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
        with open(project_info_path, "r", encoding="utf-8-sig") as file:
            project_info = json.load(file)

        logger.info("Generating AI onboarding guide")
        guide = generate_onboarding_guide(project_info)
        logger.info("AI onboarding guide generated")

        review_status_path = os.path.join(os.path.dirname(project_info_path), "senior_review.json")
        review_status = "AI Draft (Pending Senior Review)"
        approved_by = None
        if os.path.exists(review_status_path):
            try:
                with open(review_status_path, "r", encoding="utf-8") as f:
                    rdata = json.load(f)
                    if rdata.get("approved"):
                        review_status = "Senior Approved"
                        approved_by = rdata.get("approved_by")
            except Exception:
                pass

        return {
            "success": True,
            "guide": guide,
            "review_status": review_status,
            "approved_by": approved_by
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
        results = search_codebase(repository_path, query)
        return {
            "success": True,
            "query": query,
            "results": results
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Could not search repository.",
            "error": str(e)
        }


# =========================================================
# Codebase Q&A Chatbot
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
        search_results = search_codebase(repository_path, question, max_results=10)
        answer = generate_codebase_answer(
            question,
            search_results,
            conversation_history=request.conversation_history
        )

        sources = []
        for result in search_results:
            sources.append({
                "file": result["file"],
                "line": result["line"],
                "content": result.get("content", "")[:120]
            })

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


# =========================================================
# FR-17 & US-SD-02: Senior Review
# =========================================================

@app.get("/senior/review")
def get_senior_review(paths: tuple[str, str] = Depends(get_session_paths)):
    _, project_info_path = paths
    review_path = os.path.join(os.path.dirname(project_info_path), "senior_review.json")
    if not os.path.exists(review_path):
        return {
            "success": True,
            "status": "AI Draft",
            "is_approved": False,
            "approved_by": None
        }

    try:
        with open(review_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "success": True,
            "status": "Senior Approved" if data.get("approved") else "AI Draft",
            "is_approved": data.get("approved", False),
            "approved_by": data.get("approved_by"),
            "feedback": data.get("feedback", "")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/senior/review")
def submit_senior_review(
    request: SeniorReviewRequest,
    paths: tuple[str, str] = Depends(get_session_paths),
):
    _, project_info_path = paths
    review_path = os.path.join(os.path.dirname(project_info_path), "senior_review.json")
    try:
        data = {
            "approved": request.approved,
            "approved_by": request.approved_by,
            "feedback": request.feedback
        }
        os.makedirs(os.path.dirname(review_path), exist_ok=True)
        with open(review_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return {
            "success": True,
            "message": "Review status updated successfully.",
            "status": "Senior Approved" if request.approved else "AI Draft"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# =========================================================
# FR-19, US-EM-01, US-EM-02: Management Overview
# =========================================================

@app.get("/management/overview")
def management_overview(paths: tuple[str, str] = Depends(get_session_paths)):
    _, project_info_path = paths
    has_project = os.path.exists(project_info_path)
    project_name = "None"
    files_count = 0
    bus_risk = "Low"

    if has_project:
        try:
            with open(project_info_path, "r", encoding="utf-8-sig") as f:
                info = json.load(f)
                project_name = info.get("project_name", "Unknown")
                files_count = info.get("statistics", {}).get("files", 0)
                kc = info.get("knowledge_concentration", {})
                if kc.get("high_risk_modules"):
                    bus_risk = "Elevated (Single-contributor modules identified)"
        except Exception:
            pass

    return {
        "success": True,
        "aggregate_reporting": {
            "project_name": project_name,
            "total_files": files_count,
            "total_questions_asked_aggregate": 0,
            "privacy_safeguard": "Active: Developer query content is strictly hidden per US-EM-02 and DR-06",
            "onboarding_phase": "Phase 1 - Codebase Ingestion & Orientation",
            "knowledge_concentration_risk": bus_risk,
            "average_time_to_first_contribution_target": "< 2 weeks (monitored via PR events DR-05)"
        }
    }


# Mount frontend assets
if os.path.exists(FRONTEND_DIRECTORY):
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