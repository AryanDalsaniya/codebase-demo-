# Codebase Onboarding Companion

> **AI-assisted developer onboarding platform with Interactive Codebase Map, Tech Stack Detection, Knowledge Concentration, Code Evolution Timeline, Change Preview, and Source-Referenced Q&A powered by Google Gemini.**

---

## 1. Project Overview & Problem Description

When a company's senior developers have already built a software project, new junior developers who later join the team are handed a large, unfamiliar codebase and expected to become productive quickly. In practice this handover is slow and expensive:

- New hires do not know where to start and cannot easily locate the files or functions relevant to an assigned task.
- They end up repeatedly interrupting senior developers for explanations that are rarely documented or written down.
- The Engineering Manager loses visibility into how onboarding is progressing in practice.
- The organisation lacks a reliable way to shorten the time to a new developer's first meaningful contribution.

The **Codebase Onboarding Companion** is an AI-assisted platform designed to solve this problem. A developer connects a public GitHub repository, and the system:
1. Parses its files, folders, modules, functions, and cross-module dependencies into an interactive **Codebase Map**.
2. Automatically detects the technology stack, build tools, package managers, and testing libraries.
3. Generates plain-language, source-referenced explanations of how the project functions.
4. Provides a conversational **Codebase Q&A Chatbot** powered by the **Google Gemini API**, returning answers grounded directly in the repository's code with exact file and line citations (`[file:line]`).

### Core & Supporting Features
- **Interactive Codebase Map (FR-01, FR-03)**: Structural visualization of entry points, modules, architectural layers, and cross-file dependencies.
- **Technology Stack Detection (FR-02)**: Automatic detection of primary programming languages, frameworks, build systems, package managers, and test suites.
- **Knowledge Concentration (FR-15)**: Git commit and author analysis per module, surfacing expertise concentration risks and bus factor vulnerabilities.
- **Code Evolution Timeline (FR-16)**: Reconstructs chronological milestones and module development history across commits.
- **Change Preview & Impact Awareness (FR-14, US-JD-02)**: Analyzes direct dependents, indirect dependents, and affected test suites before editing a file or function.
- **Task-to-Code Guidance (FR-13)**: Translates natural-language onboarding tasks into concrete starting files, recommended functions, and execution checklists.
- **Source-Referenced Q&A Chatbot (FR-05, FR-06, US-SD-01)**: Multi-turn natural language conversation strictly grounded in retrieved code with exact clickable citations; refuses to hallucinate when context is insufficient.
- **Sensitive File Exclusion (FR-20, US-SEC-02, DR-03)**: Automatically detects and excludes secrets, credentials, `.env` files, and private keys (`*.key`, `.pem`, `id_rsa`) from AI contexts.
- **Senior Review Workflow (FR-17, US-SD-02)**: Senior developers can review, verify, and approve AI-generated onboarding guides.
- **Engineering Management Overview (FR-19, US-EM-02)**: High-level progress metrics on onboarding activities with zero developer surveillance.
- **Health & Monitoring (FR-24)**: Observability endpoint (`/health` and `/healthz`) reporting service status, version, and active capabilities.

### Stakeholder Requirements Elicitation
Requirements were elicited across seven distinct stakeholders:
1. **Junior Developer**: Guided reading order, task starting points, impact awareness before code edits.
2. **Senior Developer / Codebase Owner**: Reduced onboarding interruptions, verification controls over AI-generated guides.
3. **Engineering Manager**: Visibility into onboarding velocity and time-to-first-commit without invasive surveillance.
4. **DevOps / Platform Engineer**: Lightweight local and cloud portability, resource-bounded execution.
5. **Security Team**: Automatic exclusion of secrets (`.env`, private keys), read-only sandboxing, no credential logging.
6. **GitHub External Service**: Adherence to rate limits, branch normalization, shallow clones.
7. **LLM Provider External Service (Google Gemini)**: Token-budgeted context windows, exponential backoff, strict source grounding.

---

## 2. Technology Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2, GitPython
- **AI Inference**: **Google Gemini API** (`gemini-2.5-flash` by default, configurable via `GEMINI_MODEL`) using the official `google-genai` SDK with resilient HTTP REST fallback via `httpx`
- **Code Analysis**: Python AST parser, regex tokenizers, Git commit log graph analyzer
- **Frontend**: Vanilla HTML5, CSS3, ES6+ JavaScript (zero external bundlers or node_modules required)
- **Testing**: Python standard `unittest` suite (30 unit & integration tests)

---

## 3. How to Run on Your Computer

Follow these step-by-step instructions to set up and run the Codebase Onboarding Companion on your local computer.

### Step 1: Prerequisites

Make sure you have the following installed:
1. **Python 3.10 or newer**: Check with `python --version` (or `python3 --version`).
2. **Git**: Check with `git --version`.
3. **Google Gemini API Key**: A free API key from Google AI Studio.
   - If you don't have one yet, obtain it at: [Google AI Studio](https://aistudio.google.com/app/apikey)

---

### Step 2: Clone the Repository

```bash
git clone https://github.com/AryanDalsaniya/codebase-demo-.git
cd codebase-demo-
```

---

### Step 3: Set Up Python Virtual Environment

#### On Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### On Windows (Command Prompt):
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

#### On macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 5: Set Your Google API Key

Set the environment variable with your Gemini API key:

#### On Windows (PowerShell):
```powershell
$env:GEMINI_API_KEY = "your_actual_gemini_api_key_here"
```
*(Alternatively, you can set `$env:GOOGLE_API_KEY = "your_key"`)*

#### On Windows (Command Prompt):
```cmd
set GEMINI_API_KEY=your_actual_gemini_api_key_here
```

#### On macOS / Linux:
```bash
export GEMINI_API_KEY="your_actual_gemini_api_key_here"
```

> **Optional**: To choose a specific Gemini model (default is `gemini-2.5-flash`):
> ```powershell
> $env:GEMINI_MODEL = "gemini-2.5-flash"
> ```

---

### Step 6: Start the Backend Server

Run the FastAPI application via Uvicorn:

```bash
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

The backend server will start at:
- **API URL**: `http://127.0.0.1:8000`
- **Swagger Documentation**: `http://127.0.0.1:8000/docs`
- **Health Check**: `http://127.0.0.1:8000/health`

---

### Step 7: Launch the Web Interface

The frontend is served directly by the backend! Simply open your browser and navigate to:

👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

*(Alternatively, you can host the frontend independently using Python's built-in HTTP server)*:
```bash
python -m http.server 5500 --directory frontend
```
Then visit `http://127.0.0.1:5500`.

---

## 4. How to Use the Platform

1. **Connect a Repository**:
   - Paste any public GitHub repository link (e.g., `https://github.com/psf/requests` or `https://github.com/pallets/flask`).
   - Click **"Analyze repository"**.
   - The system performs a shallow clone, runs AST and Git metadata extraction, and populates the dashboard.

2. **Explore the Codebase Map**:
   - Scroll to **03 / Codebase Map** to see layers (Core, Utils, Tests, Config), module dependencies, and entry points.

3. **Inspect the Tech Stack**:
   - Section **04 / Tech Stack** displays identified languages, frameworks, build systems, and dependencies.

4. **Review Knowledge Concentration & Bus Factor**:
   - Section **05 / Knowledge Concentration** shows author ownership distribution per module and highlights single-contributor risk.

5. **Examine the Code Evolution Timeline**:
   - Section **06 / Evolution Timeline** traces commits, active months, and structural changes over time.

6. **Test Change Preview (Blast Radius)**:
   - Section **07 / Change Preview**: select or enter a file (e.g., `requests/api.py`), enter a symbol, and click **"Preview change impact"** to see direct/indirect dependents and affected tests.

7. **Generate Task Guidance**:
   - Section **08 / Task Guidance**: enter an onboarding task prompt (e.g., "Add custom retry backoff") to receive recommended files and an action checklist.

8. **Generate AI Onboarding Guide**:
   - Section **10 / AI Onboarding Guide**: click **"Generate guide"** to have Google Gemini synthesize a beginner-friendly architectural walkthrough.

9. **Ask Questions with Interactive Q&A**:
   - Section **11 / Conversational Codebase Q&A**: ask questions like *"Where is authentication handled?"* or *"How are exceptions formatted?"*.
   - Responses are grounded in the repository with exact clickable `[file:line]` citations.

---

## 5. Running Automated Tests

Run the full automated test suite (30 tests) anytime with:

```bash
python -m unittest discover -s tests -v
```

All tests run locally in under 1 second without requiring an active internet connection or live API key (API calls are cleanly mocked).

---

## 6. API Reference Summary

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/health` | `GET` | Health check and platform capabilities |
| `/analyze` | `POST` | Clones and indexes a public repository (`{"repo_url": "..."}`) |
| `/summary` | `GET` | Returns repository overview and file breakdown |
| `/codebase-map` | `GET` | Returns architectural layers, modules, and cross-file dependencies |
| `/tech-stack` | `GET` | Returns detected languages, frameworks, and build tools |
| `/knowledge-concentration` | `GET` | Author commit distribution and bus factor metrics |
| `/code-evolution-timeline` | `GET` | Historical commit milestones and evolution events |
| `/change-preview` | `POST` | Impact analysis: dependent files and affected tests |
| `/task-guidance` | `POST` | Task starting points and action checklists |
| `/onboarding-guide` | `GET` | Synthesizes an onboarding guide via Google Gemini |
| `/ask` | `POST` | Grounded multi-turn conversational Q&A |
| `/senior/review` | `GET`, `POST` | Senior developer guide approval workflow |
| `/management/overview` | `GET` | Aggregated onboarding progress metrics |

---

## 7. Security & Privacy Safeguards

- **Sensitive File Exclusion (FR-20)**: Patterns like `.env`, `*.key`, `*.pem`, `id_rsa`, and credential stores are blocked from AI indexing and code search.
- **Read-Only Clones**: Repositories are cloned in isolated session workspaces and never pushed back.
- **Strict Grounding**: Gemini answers enforce repository citations; ungrounded hallucinations are explicitly rejected.
