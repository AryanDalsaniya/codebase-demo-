# Codebase Onboarding Companion

An AI-assisted onboarding platform designed to bridge the gap between large, unfamiliar software repositories and new developers joining engineering teams.

---

## 1. Problem Description

When a company's senior developers have already built a software project, new junior developers who later join the team are handed a large, unfamiliar codebase and expected to become productive quickly. In practice this handover is slow and expensive: new hires do not know where to start, cannot easily locate the files or functions relevant to an assigned task, and end up repeatedly interrupting senior developers for explanations that are never written down. The Engineering Manager loses visibility into how onboarding is actually progressing, and the organisation has no reliable way to shorten the time it takes a new developer to reach their first meaningful contribution.

The **Codebase Onboarding Companion** is an AI-assisted platform designed to close this gap. A developer connects a GitHub repository, and the system parses its files, folders, modules, functions, and dependencies into an interactive **Codebase Map**, detects the technology stack, and generates plain-language, source-referenced explanations of how the project works. A conversational chatbot lets the developer ask natural-language questions and receive answers grounded in the actual code, with exact file and line citations.

Three supporting features extend this core experience:
1. **Knowledge Concentration**: Shows where historical contribution and expertise are concentrated across modules, identifying bus factor risks and recommending technical go-to owners.
2. **Code Evolution Timeline**: Reconstructs how key modules changed over the project's Git history in a readable chronological sequence.
3. **Change Preview**: Surfaces the files, dependencies, and automated test suites likely affected before a developer edits a function.

Requirements were elicited across **seven distinct stakeholders** (Junior Developer, Senior Developer / Codebase Owner, Engineering Manager, DevOps / Platform Team, Security Team, GitHub API external service, and LLM API Provider external service) to guarantee safe adoption, infrastructure resilience, and privacy preservation.

---

## 2. Core & Supporting Features

| Feature | Requirement | Description |
| :--- | :--- | :--- |
| **Interactive Codebase Map** | FR-01, FR-03 | Visualises architectural layers, entry points, component files, and module-to-module dependencies. |
| **Tech Stack Detection** | FR-02 | Detects primary languages, frameworks, package managers, build tools, and QA libraries. |
| **Knowledge Concentration** | FR-15 | Analyzes Git commit distribution by author, calculating concentration risk percentages and bus factors per module. |
| **Code Evolution Timeline** | FR-16 | Reconstructs chronological milestones and module history across commits. |
| **Change Preview / Impact** | FR-14, US-JD-02 | Calculates the blast radius (direct dependents, indirect dependents, and affected tests) prior to modifying a file. |
| **Task-to-Code Guidance** | FR-13 | Given a natural-language task prompt, suggests starting modules, key files, symbols, and an action plan. |
| **Source-Referenced Q&A** | FR-05, FR-06, US-SD-01 | Conversational chatbot grounded in repository context, citing exact `[file:line]` references. |
| **Sensitive File Exclusion** | FR-20, US-SEC-02, DR-03 | Identifies and excludes secrets (`.env`, `.pem`, `*.key`, `id_rsa`) from AI contexts and search. |
| **Governance & Dashboards** | FR-17, FR-18, FR-19, US-EM-02 | Senior approval workflow for AI guides and aggregate, privacy-preserving reporting for managers. |
| **Platform Health & Metrics** | FR-24 | Exposes `/health` endpoints and operational metadata. |

---

## 3. Technology Stack

- **Backend**: FastAPI (Python 3.10+), Pydantic v2, Uvicorn, GitPython
- **Code Intelligence**: AST analysis, regular-expression parsers, cross-module dependency analyzer
- **AI Service**: Local Llama 3.2 via Ollama (no external cloud keys required; 100% offline & zero-data-retention capable)
- **Frontend**: Vanilla JavaScript (ES6+), Semantic HTML5, CSS3 with responsive dark/light accent styling

---

## 4. Getting Started

### Prerequisites

- Python 3.10 or later
- Git installed and accessible on `PATH`
- [Ollama](https://ollama.com/) running locally with the `llama3.2` model installed:
  ```powershell
  ollama pull llama3.2
  ```

### Installation

From the project root:

```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install -r requirements.txt
```

### Running the Application

1. **Start the FastAPI Backend**:
   ```powershell
   python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
   ```
   API interactive documentation is available at <http://127.0.0.1:8000/docs>.

2. **Start the Web Frontend**:
   ```powershell
   python -m http.server 5500 --directory frontend
   ```
   Access the UI at <http://127.0.0.1:5500>.

---

## 5. API Endpoints

- `GET /health`: Health and observability status (FR-24).
- `POST /analyze`: Clones and analyzes a repository (`{ "repo_url": "..." }`).
- `GET /summary`: Returns overall repository snapshot and metrics.
- `GET /tech-stack`: Returns detected languages, frameworks, package managers, and build tools.
- `GET /codebase-map`: Returns parsed modules, layers, entry points, and graph connections.
- `GET /knowledge-concentration`: Returns commit distribution and bus factor metrics per module.
- `GET /code-evolution-timeline`: Returns commit evolution history.
- `POST /change-preview`: Calculates direct/indirect dependencies and affected tests (`{ "file_path": "...", "symbol": "..." }`).
- `POST /task-guidance`: Generates step-by-step starting guidance for a task (`{ "task": "..." }`).
- `POST /ask`: Conversational chatbot with multi-turn history and clickable source citations.
- `GET /onboarding-guide`: Generates a structured reading guide using Llama 3.2.
- `GET /senior/review` & `POST /senior/review`: Senior review and verification workflow.
- `GET /management/overview`: Privacy-preserving aggregate onboarding progress report.

---

## 6. Running Tests

Run the full automated test suite using `unittest`:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```
