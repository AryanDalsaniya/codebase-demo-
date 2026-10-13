# Codebase Onboarding Companion — Requirements Elicitation & Implementation Guide

Compiled from the **Complete Report Phase 1** (IT314 Software Engineering).

---

## 1. Problem Description
When a company's senior developers have already built a software project, new junior developers who later join the team are handed a large, unfamiliar codebase and expected to become productive quickly. In practice this handover is slow and expensive: new hires do not know where to start, cannot easily locate the files or functions relevant to an assigned task, and end up repeatedly interrupting senior developers for explanations that are never written down. The Engineering Manager loses visibility into how onboarding is actually progressing, and the organisation has no reliable way to shorten the time it takes a new developer to reach their first meaningful contribution.

The **Codebase Onboarding Companion** is an AI-assisted platform designed to close this gap. A developer connects a GitHub repository, and the system parses its files, folders, modules, functions, and dependencies into an interactive **Codebase Map**, detects the technology stack, and generates plain-language, source-referenced explanations of how the project works. A conversational chatbot lets the developer ask natural-language questions and receive answers grounded in the actual code, with exact file and line citations.

Three supporting features extend this core experience:
1. **Knowledge Concentration**: Shows where historical contribution and expertise are concentrated.
2. **Code Evolution Timeline**: Reconstructs how key modules changed over the project's Git history.
3. **Change Preview**: Surfaces the files, dependencies, and tests likely affected before a developer edits a function.

---

## 2. Seven Stakeholders Considered

1. **Junior Developer**: Primary end user blocked by unfamiliar code; needs orientation, task-to-code navigation, and trusted cited answers.
2. **Senior Developer / Codebase Owner**: Absorbs hidden onboarding friction; requires verifiable file/line citations and review workflows to trust AI summaries.
3. **Engineering Manager**: Accountable for onboarding outcomes; requires aggregate progress metrics while protecting developer privacy.
4. **DevOps / Platform / IT Team**: Manages infrastructure; requires shallow clones, worker offloading, and rate-limit safeguards.
5. **Security Team**: Protects intellectual property; mandates authentication and strict exclusion of secrets (`.env`, private keys) from AI context.
6. **GitHub (External Service)**: Constrained by REST API quotas, permissions, and shallow cloning.
7. **LLM / AI API Provider (External Service)**: Constrained by token limits, structured schema enforcement, and zero-data-retention compliance.

---

## 3. Implementation Matrix

| Requirement | Implementation Component | Status |
| :--- | :--- | :--- |
| **FR-01: Repo Connection & Analysis** | `analyzer/repository_loader.py`, `backend/main.py: /analyze` | Implemented |
| **FR-02: Tech Stack Detection** | `analyzer/repository_analyzer.py: detect_tech_stack`, `GET /tech-stack` | Implemented |
| **FR-03: Codebase Map** | `analyzer/repository_analyzer.py: generate_codebase_map`, `GET /codebase-map` | Implemented |
| **FR-04: Code Search** | `analyzer/code_search.py: search_codebase`, `GET /search` | Implemented |
| **FR-05: Conversational Q&A** | `backend/qa_service.py`, `backend/main.py: POST /ask` | Implemented |
| **FR-06: Source-Referenced Answers** | `backend/qa_service.py` (`[file:line]`), `frontend/script.js` | Implemented |
| **FR-13: Task-to-Code Guidance** | `analyzer/task_guidance.py`, `backend/main.py: POST /task-guidance` | Implemented |
| **FR-14: Change Preview** | `analyzer/impact_analyzer.py`, `backend/main.py: POST /change-preview` | Implemented |
| **FR-15: Knowledge Concentration** | `analyzer/repository_analyzer.py: analyze_git_history`, `GET /knowledge-concentration` | Implemented |
| **FR-16: Code Evolution Timeline** | `analyzer/repository_analyzer.py: analyze_git_history`, `GET /code-evolution-timeline` | Implemented |
| **FR-17: Review & Approval Workflow** | `backend/main.py: /senior/review` | Implemented |
| **FR-19: Management Reporting** | `backend/main.py: /management/overview` | Implemented |
| **FR-20: Secret Exclusion** | `analyzer/code_search.py`, `analyzer/repository_analyzer.py: scan_sensitive_files` | Implemented |
| **FR-24: Platform Reliability** | `backend/main.py: /health` | Implemented |

