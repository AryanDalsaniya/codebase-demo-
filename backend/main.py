from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import os
import json
import logging
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
REPOSITORY_PATH = os.path.join(DATA_DIRECTORY, "cloned_repo")
PROJECT_INFO_PATH = os.path.join(DATA_DIRECTORY, "project_info.json")
SENIOR_REVIEW_PATH = os.path.join(DATA_DIRECTORY, "senior_review.json")
METRICS_PATH = os.path.join(DATA_DIRECTORY, "management_metrics.json")
logger = logging.getLogger(__name__)


# =========================================================
# FastAPI Application
# =========================================================

app = FastAPI(
    title="Codebase Onboarding Companion",
    description="AI-powered tool for understanding unfamiliar codebases (Phase 1)",
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
    repo_url: str = Field(min_length=1, max_length=2048)


class QuestionRequest(BaseModel):
    question: str
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
# Helpers
# =========================================================

def record_query_metric(topic: str = "general"):
    """Aggregate metrics tracking without storing individual developer question content (US-EM-02 / DR-06)."""
    try:
        metrics = {"total_queries": 0, "topics": {}}
        if os.path.exists(METRICS_PATH):
            with open(METRICS_PATH, "r", encoding="utf-8") as f:
                metrics = json.load(f)
        metrics["total_queries"] = metrics.get("total_queries", 0) + 1
        topics = metrics.get("topics", {})
        topics[topic] = topics.get(topic, 0) + 1
        metrics["topics"] = topics
        with open(METRICS_PATH, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
    except Exception:
        pass


# =========================================================
# Health & Status (FR-24)
# =========================================================

@app.get("/")
def home():
    return {
        "message": "Codebase Onboarding Companion API",
        "status": "running",
        "version": "1.0"
    }


@app.get("/health")
def health_check():
    """FR-24: Platform Reliability Operations - exposes health and observability endpoint."""
    return {
        "status": "healthy",
        "service": "Codebase Onboarding Companion",
        "repository_analyzed": os.path.exists(PROJECT_INFO_PATH),
        "cloned_repo_present": os.path.exists(REPOSITORY_PATH),
        "version": "1.0"
    }


# =========================================================
# Analyze Repository
# =========================================================

@app.post("/analyze")
def analyze_repository(request: RepositoryRequest):
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
            REPOSITORY_PATH,
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
        logger.info("Analyzing repository at %s", REPOSITORY_PATH)
        project_info = generate_project_info(REPOSITORY_PATH)
        os.makedirs(DATA_DIRECTORY, exist_ok=True)
        save_project_info(project_info, PROJECT_INFO_PATH)
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
def get_summary():
    if not os.path.exists(PROJECT_INFO_PATH):
        return {
            "success": False,
            "message": "No repository has been analyzed yet."
        }

    try:
        with open(PROJECT_INFO_PATH, "r", encoding="utf-8-sig") as file:
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
def get_tech_stack():
    """FR-02: Detect and display the primary languages, frameworks, libraries, and package managers."""
    if not os.path.exists(PROJECT_INFO_PATH):
        return {"success": False, "message": "Please analyze a repository first."}

    try:
        with open(PROJECT_INFO_PATH, "r", encoding="utf-8-sig") as file:
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
def get_codebase_map():
    """FR-03: Present an organised interactive Codebase Map highlighting key modules, entry points, and layers."""
    if not os.path.exists(PROJECT_INFO_PATH):
        return {"success": False, "message": "Please analyze a repository first."}

    try:
        with open(PROJECT_INFO_PATH, "r", encoding="utf-8-sig") as file:
            project_info = json.load(file)
        return {
            "success": True,
            "codebase_map": project_info.get("codebase_map", {})
        }
    except Exception as e:
        return {"success": False, "message": "Could not read codebase map.", "error": str(e)}


# =========================================================
# FR-15: Supporting Feature - Knowledge Concentration
# =========================================================

@app.get("/knowledge-concentration")
def get_knowledge_concentration():
    """FR-15: Show where historical contribution and code expertise are concentrated, based on commit history."""
    if not os.path.exists(PROJECT_INFO_PATH):
        return {"success": False, "message": "Please analyze a repository first."}

    try:
        with open(PROJECT_INFO_PATH, "r", encoding="utf-8-sig") as file:
            project_info = json.load(file)
        return {
            "success": True,
            "knowledge_concentration": project_info.get("knowledge_concentration", {})
        }
    except Exception as e:
        return {"success": False, "message": "Could not read knowledge concentration.", "error": str(e)}


# =========================================================
# FR-16: Supporting Feature - Code Evolution Timeline
# =========================================================

@app.get("/code-evolution-timeline")
def get_code_evolution_timeline(module: Optional[str] = None):
    """FR-16: Reconstruct how key modules changed over the project's Git history."""
    if not os.path.exists(PROJECT_INFO_PATH):
        return {"success": False, "message": "Please analyze a repository first."}

    try:
        with open(PROJECT_INFO_PATH, "r", encoding="utf-8-sig") as file:
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
# FR-14: Supporting Feature - Change Preview / Impact Awareness
# =========================================================

@app.post("/change-preview")
def change_preview(request: ChangePreviewRequest):
    """FR-14 & US-JD-02: Before a file is modified, list the other files, modules, and tests likely affected."""
    if not os.path.exists(REPOSITORY_PATH):
        return {"success": False, "message": "Please analyze a repository first."}

    try:
        impact = analyze_change_impact(
            REPOSITORY_PATH,
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
def task_guidance(request: TaskGuidanceRequest):
    """FR-13: Given a short task description, point the developer to the relevant module, files, and functions."""
    if not os.path.exists(REPOSITORY_PATH) or not os.path.exists(PROJECT_INFO_PATH):
        return {"success": False, "message": "Please analyze a repository first."}

    try:
        with open(PROJECT_INFO_PATH, "r", encoding="utf-8-sig") as file:
            project_info = json.load(file)
        guidance = generate_task_guidance(REPOSITORY_PATH, project_info, request.task)
        return guidance
    except Exception as e:
        logger.exception("Task guidance failed")
        return {"success": False, "message": "Could not generate task guidance.", "error": str(e)}


# =========================================================
# File Tree & File Viewer
# =========================================================

@app.get("/file-tree")
def get_file_tree():
    if not os.path.exists(PROJECT_INFO_PATH):
        return {
            "success": False,
            "message": "Please analyze a repository first."
        }

    try:
        with open(PROJECT_INFO_PATH, "r", encoding="utf-8-sig") as file:
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
def onboarding_guide():
    if not os.path.exists(PROJECT_INFO_PATH):
        return {
            "success": False,
            "message": "Please analyze a repository first."
        }

    try:
        with open(PROJECT_INFO_PATH, "r", encoding="utf-8-sig") as file:
            project_info = json.load(file)

        guide = generate_onboarding_guide(project_info)

        # Check senior review status (US-SD-02)
        review_status = "AI Draft (Pending Senior Review)"
        approved_by = None
        if os.path.exists(SENIOR_REVIEW_PATH):
            try:
                with open(SENIOR_REVIEW_PATH, "r", encoding="utf-8") as f:
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
    except Exception as e:
        logger.exception("Could not generate guide")
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
        results = search_codebase(REPOSITORY_PATH, query)
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
# Codebase Q&A Chatbot (FR-05, FR-06, US-SD-01)
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
        # Search repository for grounding code (excludes sensitive files)
        search_results = search_codebase(REPOSITORY_PATH, question, max_results=10)

        # Record metric without storing private question text (US-EM-02 / DR-06)
        record_query_metric(topic="codebase_qna")

        # Generate grounded answer with conversational history retention (FR-05)
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
    except Exception as e:
        logger.exception("Q&A failed")
        return {
            "success": False,
            "message": "Could not answer the question.",
            "error": str(e)
        }


# =========================================================
# FR-17 & US-SD-02: Review & Approval Workflow
# =========================================================

@app.get("/senior/review")
def get_senior_review_status():
    """US-SD-02: Check whether generated summaries are AI-only drafts or Senior-approved."""
    if not os.path.exists(SENIOR_REVIEW_PATH):
        return {
            "success": True,
            "status": "AI Draft",
            "is_approved": False,
            "approved_by": None
        }

    try:
        with open(SENIOR_REVIEW_PATH, "r", encoding="utf-8") as f:
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
def submit_senior_review(request: SeniorReviewRequest):
    """FR-17 & US-SD-02: Allow senior developer to review, correct, or approve an AI explanation."""
    try:
        data = {
            "approved": request.approved,
            "approved_by": request.approved_by,
            "feedback": request.feedback
        }
        with open(SENIOR_REVIEW_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return {
            "success": True,
            "message": "Review status updated successfully.",
            "status": "Senior Approved" if request.approved else "AI Draft"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# =========================================================
# FR-19, US-EM-01, US-EM-02: Management Reporting Dashboard
# =========================================================

@app.get("/management/overview")
def management_overview():
    """
    FR-19, US-EM-01, US-EM-02, DR-06: Aggregate onboarding progress & outcome metrics.
    Individual developer queries remain strictly private from management by default.
    """
    total_queries = 0
    if os.path.exists(METRICS_PATH):
        try:
            with open(METRICS_PATH, "r", encoding="utf-8") as f:
                metrics_data = json.load(f)
                total_queries = metrics_data.get("total_queries", 0)
        except Exception:
            pass

    has_project = os.path.exists(PROJECT_INFO_PATH)
    project_name = "None"
    files_count = 0
    bus_risk = "Low"

    if has_project:
        try:
            with open(PROJECT_INFO_PATH, "r", encoding="utf-8-sig") as f:
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
            "total_questions_asked_aggregate": total_queries,
            "privacy_safeguard": "Active: Developer query content is strictly hidden per US-EM-02 and DR-06",
            "onboarding_phase": "Phase 1 - Codebase Ingestion & Orientation",
            "knowledge_concentration_risk": bus_risk,
            "average_time_to_first_contribution_target": "< 2 weeks (monitored via PR events DR-05)"
        }
    }


# =========================================================
# Run Server
# =========================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)