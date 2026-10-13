"use strict";

/*
=========================================================
CODEBASE ONBOARDING COMPANION (PHASE 1)
=========================================================
Integrated client script supporting:
- Core scanning & Codebase Map (FR-01, FR-03)
- Technology Stack Detection (FR-02)
- Knowledge Concentration (FR-15)
- Code Evolution Timeline (FR-16)
- Change Preview / Impact Awareness (FR-14)
- Task-to-Code Guidance (FR-13)
- Grounded Source-Referenced Q&A Chatbot (FR-05, FR-06)
- Senior Review & Management Visibility (FR-17, FR-19)
=========================================================
*/

const API_BASE = "http://127.0.0.1:8000";
let conversationHistory = [];

/* ========================================================
   DOM HELPERS
======================================================== */

function getElement(id) {
    return document.getElementById(id);
}

function show(element) {
    if (element) {
        element.classList.remove("hidden");
    }
}

function hide(element) {
    if (element) {
        element.classList.add("hidden");
    }
}

function setText(id, value) {
    const el = getElement(id);
    if (!el) return;
    el.textContent = (value === undefined || value === null || value === "") ? "—" : String(value);
}

function showError(message) {
    const error = getElement("error");
    if (!error) return;
    error.textContent = message;
    show(error);
}

function clearError() {
    const error = getElement("error");
    if (!error) return;
    error.textContent = "";
    hide(error);
}

/* ========================================================
   API REQUEST WRAPPER
======================================================== */

async function apiRequest(endpoint, options = {}) {
    let response;
    try {
        response = await fetch(API_BASE + endpoint, options);
    } catch (error) {
        if (error instanceof TypeError) {
            throw new Error("Could not reach API. Please ensure backend is running at http://127.0.0.1:8000");
        }
        throw error;
    }

    let data;
    try {
        data = await response.json();
    } catch {
        throw new Error(`Backend returned an invalid response (${response.status}).`);
    }

    if (!response.ok) {
        throw new Error(data.detail || data.error || data.message || `Request failed (${response.status}).`);
    }

    if (data.success === false) {
        throw new Error(data.message || "The backend could not complete this request.");
    }

    return data;
}

/* ========================================================
   REPOSITORY ANALYSIS
======================================================== */

async function analyzeRepository() {
    const repoInput = getElement("repoUrl");
    const analyzeButton = getElement("analyzeButton");
    const loading = getElement("loading");
    const result = getElement("result");

    const repoUrl = repoInput ? repoInput.value.trim() : "";
    if (!repoUrl) {
        showError("Please enter a GitHub repository URL.");
        return;
    }

    clearError();
    hide(result);
    show(loading);
    if (analyzeButton) analyzeButton.disabled = true;

    try {
        // Step 1: Clone and analyze
        await apiRequest("/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ repo_url: repoUrl })
        });

        // Step 2: Fetch comprehensive summary
        const summary = await apiRequest("/summary");
        displaySummary(summary);

        // Step 3: Fetch file tree
        await loadRepositoryFileTree();

        // Step 4: Show results
        show(result);

        // Step 5: Load Senior & Manager views
        await loadSeniorReviewStatus();
        await loadManagementOverview();

    } catch (error) {
        console.error("Analysis error:", error);
        showError(error.message || "Could not analyze the repository.");
    } finally {
        hide(loading);
        if (analyzeButton) analyzeButton.disabled = false;
    }
}

/* ========================================================
   DISPLAY SUMMARY & CORE MODULES
======================================================== */

function displaySummary(summary) {
    if (!summary) return;

    // Project Name & Counts
    setText("projectName", summary.project_name || "Unknown");
    const stats = summary.statistics || {};
    setText("fileCount", stats.files ?? 0);
    setText("directoryCount", stats.directories ?? 0);

    const languages = summary.languages || {};
    setText("languageCount", Object.keys(languages).length);
    setText("classCount", stats.total_classes ?? summary.classes ?? 0);
    setText("functionCount", stats.total_functions ?? summary.functions ?? 0);

    // Security Scan Status (FR-20)
    const sec = summary.security_scan || {};
    const secBadge = getElement("securityBadge");
    if (secBadge) {
        secBadge.textContent = sec.status || "🔒 Secrets Excluded from AI";
    }

    // Description
    const descEl = getElement("projectDescription");
    if (descEl) {
        descEl.textContent = summary.readme
            ? (summary.readme.length > 800 ? summary.readme.substring(0, 800) + "..." : summary.readme)
            : "Repository analyzed successfully.";
    }

    // Pre-populate Change Preview file input with primary file if available
    const importantFiles = summary.important_files || [];
    if (importantFiles.length > 0) {
        const impactInput = getElement("impactFileInput");
        if (impactInput && !impactInput.value) {
            impactInput.value = importantFiles[0].file || importantFiles[0];
        }
    }

    // Display sub-features
    displayCodebaseMap(summary.codebase_map || {});
    displayTechStack(summary.tech_stack || {});
    displayKnowledgeConcentration(summary.knowledge_concentration || {});
    displayCodeEvolutionTimeline(summary.code_evolution_timeline || {});
}

/* ========================================================
   FR-03: DISPLAY INTERACTIVE CODEBASE MAP
======================================================== */

function displayCodebaseMap(map) {
    const entryList = getElement("entryPointsList");
    const layersContainer = getElement("mapLayersContainer");
    const connList = getElement("connectionsList");

    if (entryList) {
        entryList.innerHTML = "";
        const entries = map.entry_points || [];
        if (entries.length === 0) {
            entryList.innerHTML = `<span class="entry-point-chip" style="background:#555;">No standard main entry file detected</span>`;
        } else {
            entries.forEach(ep => {
                const chip = document.createElement("span");
                chip.className = "entry-point-chip";
                chip.textContent = `▶ ${ep.file}`;
                chip.title = ep.reason;
                chip.addEventListener("click", () => {
                    loadFile(ep.file);
                    const el = getElement("section-explorer");
                    if (el) el.scrollIntoView({ behavior: "smooth" });
                });
                entryList.appendChild(chip);
            });
        }
    }

    if (layersContainer) {
        layersContainer.innerHTML = "";
        const modules = map.modules || [];
        const layers = map.layers || {};

        Object.keys(layers).forEach(layerName => {
            const card = document.createElement("div");
            card.className = "map-layer-card";

            const title = document.createElement("div");
            title.className = "layer-title";
            title.textContent = layerName;
            card.appendChild(title);

            const modContainer = document.createElement("div");
            modContainer.className = "layer-modules";

            const moduleNames = layers[layerName] || [];
            moduleNames.forEach(modName => {
                const modData = modules.find(m => m.name === modName || m.id === modName) || {
                    name: modName,
                    file_count: "—",
                    description: "Module component"
                };

                const item = document.createElement("div");
                item.className = "map-module-item";
                item.innerHTML = `
                    <div class="module-header">
                        <span class="module-name">📦 ${modData.name}</span>
                        <span style="font-size: 11px; font-weight: 700; color: #4b6b3e;">${modData.file_count} files</span>
                    </div>
                    <div class="module-meta">${modData.description || "Module"}</div>
                `;

                item.addEventListener("click", () => {
                    const impactInput = getElement("impactFileInput");
                    if (impactInput && modData.key_files && modData.key_files.length > 0) {
                        impactInput.value = modData.key_files[0];
                    }
                    if (modData.key_files && modData.key_files.length > 0) {
                        loadFile(modData.key_files[0]);
                    }
                });

                modContainer.appendChild(item);
            });

            card.appendChild(modContainer);
            layersContainer.appendChild(card);
        });
    }

    if (connList) {
        connList.innerHTML = "";
        const conns = map.connections || [];
        conns.forEach(c => {
            const span = document.createElement("span");
            span.className = "connection-edge";
            span.textContent = `${c.from} ➔ ${c.to} (${c.label})`;
            connList.appendChild(span);
        });
    }
}

/* ========================================================
   FR-02: DISPLAY TECHNOLOGY STACK
======================================================== */

function displayTechStack(tech) {
    function populate(id, items) {
        const container = getElement(id);
        if (!container) return;
        container.innerHTML = "";
        const list = Array.isArray(items) ? items : [items];
        if (list.length === 0 || !list[0]) {
            container.innerHTML = `<span class="tech-badge" style="color:#888;">None detected</span>`;
            return;
        }
        list.forEach(item => {
            const badge = document.createElement("span");
            badge.className = "tech-badge";
            badge.textContent = item;
            container.appendChild(badge);
        });
    }

    populate("techLanguages", tech.languages || []);
    populate("techFrameworks", tech.frameworks || []);
    populate("techPackageManagers", tech.package_managers || []);
    populate("techBuildTools", tech.build_tools || []);
    populate("techTesting", tech.testing_tools || []);
}

/* ========================================================
   FR-15: DISPLAY KNOWLEDGE CONCENTRATION
======================================================== */

function displayKnowledgeConcentration(kc) {
    const alertBox = getElement("busFactorAlert");
    if (alertBox) {
        alertBox.textContent = kc.bus_factor_alert || "Knowledge contribution metrics calculated.";
    }

    const contribList = getElement("contributorsList");
    if (contribList) {
        contribList.innerHTML = "";
        const contributors = kc.contributors || [];
        contributors.forEach(c => {
            const card = document.createElement("div");
            card.className = "contributor-card";
            card.innerHTML = `
                <div class="contributor-name">👤 ${c.author}</div>
                <div class="contributor-role">${c.role || "Contributor"}</div>
                <div style="font-size: 12px; display: flex; justify-content: space-between;">
                    <span>${c.commits} commits</span>
                    <strong>${c.percentage}%</strong>
                </div>
                <div class="bar-wrapper">
                    <div class="bar-fill" style="width: ${c.percentage}%;"></div>
                </div>
                <div style="font-size: 11px; color: var(--muted); margin-top: 4px;">
                    ${c.files_touched_count} files modified
                </div>
            `;
            contribList.appendChild(card);
        });
    }

    const grid = getElement("moduleOwnershipGrid");
    if (grid) {
        grid.innerHTML = "";
        const ownerships = kc.module_ownership || [];
        ownerships.forEach(o => {
            const card = document.createElement("div");
            card.className = "ownership-card";
            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <strong style="font-size: 13px;">${o.module}</strong>
                    <span class="badge-risk" style="background: ${o.risk_color};">${o.risk_level} Risk</span>
                </div>
                <div style="font-size: 12px; margin-bottom: 4px;">
                    Lead Contributor: <strong>${o.primary_owner}</strong> (${o.concentration_percentage}%)
                </div>
                <div style="font-size: 11px; color: var(--muted);">
                    ${o.recommendation}
                </div>
            `;
            grid.appendChild(card);
        });
    }
}

/* ========================================================
   FR-16: DISPLAY CODE EVOLUTION TIMELINE
======================================================== */

function displayCodeEvolutionTimeline(timeline) {
    const container = getElement("timelineContainer");
    if (!container) return;
    container.innerHTML = "";

    const events = timeline.events || [];
    if (events.length === 0) {
        container.innerHTML = `<p style="font-size: 13px; color: var(--muted);">No Git commit history available.</p>`;
        return;
    }

    events.forEach(ev => {
        const node = document.createElement("div");
        node.className = "timeline-node";

        let tagClass = "tag-update";
        if (ev.type === "Feature") tagClass = "tag-feature";
        else if (ev.type === "Bug Fix") tagClass = "tag-bug-fix";
        else if (ev.type === "Refactor") tagClass = "tag-refactor";

        node.innerHTML = `
            <div class="timeline-content-card">
                <div class="timeline-meta">
                    <span class="timeline-tag ${tagClass}">${ev.type}</span>
                    <strong style="font-family: Consolas, monospace;">${ev.hash}</strong>
                    <span>• ${ev.author}</span>
                    <span>• ${ev.date}</span>
                </div>
                <div class="timeline-title">${ev.message}</div>
                <div style="font-size: 11px; color: var(--muted); margin-top: 6px;">
                    Touched ${ev.files_count} file(s)${ev.files && ev.files.length > 0 ? ': ' + ev.files.join(', ') : ''}
                </div>
            </div>
        `;
        container.appendChild(node);
    });
}

/* ========================================================
   FR-14 & US-JD-02: CHANGE PREVIEW / IMPACT AWARENESS
======================================================== */

async function analyzeChangeImpact() {
    const fileInput = getElement("impactFileInput");
    const symbolInput = getElement("impactSymbolInput");
    const button = getElement("analyzeImpactButton");
    const resultBox = getElement("impactResults");

    const filePath = fileInput ? fileInput.value.trim() : "";
    const symbol = symbolInput ? symbolInput.value.trim() : "";

    if (!filePath) {
        showError("Please enter a target file path to preview change impact.");
        return;
    }

    clearError();
    if (button) button.disabled = true;

    try {
        const data = await apiRequest("/change-preview", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ file_path: filePath, symbol: symbol || null })
        });

        // Set counts & badges
        setText("directCountBadge", data.direct_dependents_count);
        setText("indirectCountBadge", data.indirect_dependents_count);
        setText("testsCountBadge", data.affected_tests_count);

        const riskBadge = getElement("riskLevelBadge");
        if (riskBadge) {
            riskBadge.textContent = `${data.risk_level} Risk`;
            riskBadge.style.background = data.risk_color || "#333";
        }

        // Direct Dependents list
        const directList = getElement("directDependentsList");
        if (directList) {
            directList.innerHTML = "";
            if (data.direct_dependents.length === 0) {
                directList.innerHTML = `<span style="font-size: 12px; color: var(--muted);">No direct dependents found.</span>`;
            } else {
                data.direct_dependents.forEach(d => {
                    const item = document.createElement("div");
                    item.className = "impact-item";
                    item.innerHTML = `<strong>${d.file}</strong><br><span style="font-size:11px; color:var(--muted);">${d.reason}</span>`;
                    item.addEventListener("click", () => loadFile(d.file));
                    directList.appendChild(item);
                });
            }
        }

        // Indirect Dependents list
        const indirectList = getElement("indirectDependentsList");
        if (indirectList) {
            indirectList.innerHTML = "";
            if (data.indirect_dependents.length === 0) {
                indirectList.innerHTML = `<span style="font-size: 12px; color: var(--muted);">No indirect dependents found.</span>`;
            } else {
                data.indirect_dependents.forEach(d => {
                    const item = document.createElement("div");
                    item.className = "impact-item";
                    item.innerHTML = `<strong>${d.file}</strong><br><span style="font-size:11px; color:var(--muted);">${d.reason}</span>`;
                    item.addEventListener("click", () => loadFile(d.file));
                    indirectList.appendChild(item);
                });
            }
        }

        // Affected tests list
        const testsList = getElement("affectedTestsList");
        if (testsList) {
            testsList.innerHTML = "";
            if (data.affected_tests.length === 0) {
                testsList.innerHTML = `<span style="font-size: 12px; color: #dc2626;">⚠️ No automated tests found covering this component!</span>`;
            } else {
                data.affected_tests.forEach(t => {
                    const item = document.createElement("div");
                    item.className = "impact-item";
                    item.style.borderColor = "#bae6fd";
                    item.innerHTML = `<strong>🧪 ${t.file}</strong><br><span style="font-size:11px; color:var(--muted);">${t.reason}</span>`;
                    item.addEventListener("click", () => loadFile(t.file));
                    testsList.appendChild(item);
                });
            }
        }

        // Recommendations
        const recList = getElement("impactRecommendations");
        if (recList) {
            recList.innerHTML = "";
            (data.recommendations || []).forEach(r => {
                const rec = document.createElement("div");
                rec.style.fontSize = "12.5px";
                rec.style.lineHeight = "1.6";
                rec.textContent = `• ${r}`;
                recList.appendChild(rec);
            });
        }

        show(resultBox);

    } catch (err) {
        showError(err.message || "Failed to preview change impact.");
    } finally {
        if (button) button.disabled = false;
    }
}

/* ========================================================
   FR-13: TASK-TO-CODE GUIDANCE
======================================================== */

async function getTaskGuidance() {
    const input = getElement("taskInput");
    const button = getElement("taskGuideButton");
    const resultBox = getElement("taskGuideResult");

    const taskText = input ? input.value.trim() : "";
    if (!taskText) {
        showError("Please enter a short task description.");
        return;
    }

    clearError();
    if (button) button.disabled = true;

    try {
        const data = await apiRequest("/task-guidance", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ task: taskText })
        });

        const primaryFileEl = getElement("taskPrimaryFile");
        if (primaryFileEl) {
            primaryFileEl.textContent = data.primary_file;
            primaryFileEl.onclick = () => loadFile(data.primary_file);
        }

        setText("taskPrimaryModule", data.primary_module);

        const stepsContainer = getElement("taskPlanSteps");
        if (stepsContainer) {
            stepsContainer.innerHTML = "";
            (data.action_plan || []).forEach(step => {
                const div = document.createElement("div");
                div.className = "plan-step";
                div.textContent = step;
                stepsContainer.appendChild(div);
            });
        }

        show(resultBox);

    } catch (err) {
        showError(err.message || "Could not generate task guidance.");
    } finally {
        if (button) button.disabled = false;
    }
}

/* ========================================================
   FILE TREE & VIEWER
======================================================== */

async function loadRepositoryFileTree() {
    const container = getElement("fileTree");
    if (!container) return;
    container.innerHTML = "Loading files...";

    try {
        const data = await apiRequest("/file-tree");
        const tree = data.file_tree || [];
        container.innerHTML = "";

        if (tree.length === 0) {
            container.textContent = "No files found.";
            return;
        }

        renderFileTree(tree, container);
    } catch (error) {
        container.textContent = "Could not load file tree.";
    }
}

function renderFileTree(items, container, parentPath = "") {
    if (!Array.isArray(items)) return;

    items.forEach(item => {
        if (!item) return;
        const name = item.name || "Unknown";
        const currentPath = parentPath ? `${parentPath}/${name}` : name;

        if (item.type === "directory" || Array.isArray(item.children)) {
            const wrapper = document.createElement("div");
            const directory = document.createElement("div");
            directory.className = "tree-item tree-directory";
            directory.textContent = `📁 ${name}`;
            wrapper.appendChild(directory);

            const children = document.createElement("div");
            children.className = "tree-children";
            renderFileTree(item.children || [], children, currentPath);
            wrapper.appendChild(children);

            directory.addEventListener("click", () => {
                children.style.display = (children.style.display === "none") ? "block" : "none";
            });

            container.appendChild(wrapper);
        } else {
            const file = document.createElement("div");
            file.className = "tree-item tree-file";
            file.textContent = `📄 ${name}`;
            file.addEventListener("click", () => loadFile(currentPath));
            container.appendChild(file);
        }
    });
}

async function loadFile(filePath, targetLine = null) {
    const contentElement = getElement("fileContent");
    const pathElement = getElement("filePath");
    if (!contentElement) return;

    contentElement.textContent = "Loading file...";
    if (pathElement) pathElement.textContent = filePath;

    try {
        const data = await apiRequest(`/file?path=${encodeURIComponent(filePath)}`);
        const content = data.content ?? "";
        contentElement.textContent = content || "This file is empty.";

        // Highlight line if specified (e.g. from citation click)
        if (targetLine) {
            const lines = content.split("\n");
            let lineIdx = parseInt(targetLine, 10);
            if (!isNaN(lineIdx) && lineIdx > 0 && lineIdx <= lines.length) {
                // Focus explorer section
                const explorerSec = getElement("section-explorer");
                if (explorerSec) explorerSec.scrollIntoView({ behavior: "smooth" });
            }
        }
    } catch (error) {
        contentElement.textContent = `Could not load file.\n\n${error.message}`;
    }
}

/* ========================================================
   AI ONBOARDING GUIDE
======================================================== */

async function generateOnboardingGuide() {
    const button = getElement("generateGuideButton");
    const loading = getElement("guideLoading");
    const error = getElement("guideError");
    const guide = getElement("onboardingGuide");

    hide(error);
    hide(guide);
    show(loading);
    if (button) button.disabled = true;

    try {
        const data = await apiRequest("/onboarding-guide");
        const guideText = data.guide || "";
        if (!guideText) throw new Error("The onboarding guide returned empty.");
        guide.textContent = guideText;
        show(guide);

        const statusBadge = getElement("guideReviewStatusBadge");
        if (statusBadge) {
            statusBadge.textContent = data.review_status || "AI Draft";
        }
    } catch (err) {
        if (error) {
            error.textContent = err.message || "Could not generate onboarding guide.";
            show(error);
        }
    } finally {
        hide(loading);
        if (button) button.disabled = false;
    }
}

/* ========================================================
   CONVERSATIONAL CODEBASE Q&A (FR-05, FR-06, US-SD-01)
======================================================== */

async function askQuestion() {
    const input = getElement("questionInput");
    const button = getElement("askButton");
    const loading = getElement("qaLoading");
    const error = getElement("qaError");
    const thread = getElement("chatThread");

    const question = input ? input.value.trim() : "";
    if (!question) {
        showError("Please enter a question.");
        return;
    }

    clearError();
    hide(error);
    show(loading);
    if (button) button.disabled = true;

    // Append user bubble to thread
    if (thread) {
        const userBubble = document.createElement("div");
        userBubble.className = "chat-bubble chat-bubble-user";
        userBubble.textContent = question;
        thread.appendChild(userBubble);
        thread.scrollTop = thread.scrollHeight;
    }

    try {
        const data = await apiRequest("/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                question: question,
                conversation_history: conversationHistory
            })
        });

        // Retain conversational context (FR-05)
        conversationHistory.push({ role: "user", content: question });
        conversationHistory.push({ role: "assistant", content: data.answer || "" });

        if (thread) {
            const assistantBubble = document.createElement("div");
            assistantBubble.className = "chat-bubble chat-bubble-assistant";

            const textDiv = document.createElement("div");
            textDiv.textContent = data.answer || "No response received.";
            assistantBubble.appendChild(textDiv);

            // Grounded clickable citations (FR-06, US-SD-01)
            const sources = data.sources || [];
            if (sources.length > 0) {
                const citationsDiv = document.createElement("div");
                citationsDiv.style.marginTop = "12px";
                citationsDiv.style.borderTop = "1px solid #e5eee2";
                citationsDiv.style.paddingTop = "8px";

                const label = document.createElement("div");
                label.style.fontSize = "11px";
                label.style.fontWeight = "700";
                label.style.color = "#3a5f2e";
                label.textContent = "VERIFIABLE SOURCES (CLICK TO INSPECT):";
                citationsDiv.appendChild(label);

                sources.forEach(src => {
                    const pill = document.createElement("span");
                    pill.className = "citation-pill";
                    pill.textContent = `📍 ${src.file}:${src.line}`;
                    pill.title = `Inspect ${src.file} at line ${src.line}`;
                    pill.addEventListener("click", () => {
                        loadFile(src.file, src.line);
                    });
                    citationsDiv.appendChild(pill);
                });

                assistantBubble.appendChild(citationsDiv);
            }

            thread.appendChild(assistantBubble);
            thread.scrollTop = thread.scrollHeight;
        }

        if (input) input.value = "";

    } catch (err) {
        if (error) {
            error.textContent = err.message || "Could not answer question.";
            show(error);
        }
    } finally {
        hide(loading);
        if (button) button.disabled = false;
    }
}

/* ========================================================
   SENIOR REVIEW & MANAGEMENT DASHBOARDS
======================================================== */

async function loadSeniorReviewStatus() {
    try {
        const data = await apiRequest("/senior/review");
        const statusEl = getElement("seniorApprovalDisplay");
        if (statusEl) {
            statusEl.textContent = data.is_approved ? `Approved by ${data.approved_by || 'Senior'}` : "AI Draft (Pending Review)";
            statusEl.style.color = data.is_approved ? "#166534" : "#b45309";
        }
    } catch {
        // Non-blocking
    }
}

async function approveSeniorReview() {
    const button = getElement("seniorApproveButton");
    if (button) button.disabled = true;

    try {
        await apiRequest("/senior/review", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                approved: true,
                feedback: "Reviewed and approved for new hire onboarding.",
                approved_by: "Senior Codebase Owner"
            })
        });

        await loadSeniorReviewStatus();
        const badge = getElement("guideReviewStatusBadge");
        if (badge) badge.textContent = "Senior Approved";

    } catch (err) {
        showError("Failed to update senior review: " + err.message);
    } finally {
        if (button) button.disabled = false;
    }
}

async function loadManagementOverview() {
    try {
        const data = await apiRequest("/management/overview");
        const reporting = data.aggregate_reporting || {};
        setText("mgmtQueriesCount", reporting.total_questions_asked_aggregate ?? 0);
    } catch {
        // Non-blocking
    }
}

/* ========================================================
   INITIALIZATION
======================================================== */

document.addEventListener("DOMContentLoaded", () => {
    console.log("Codebase Onboarding Companion (Phase 1) Initialized.");

    // Analyze Button
    const analyzeBtn = getElement("analyzeButton");
    if (analyzeBtn) analyzeBtn.addEventListener("click", analyzeRepository);

    // Enter key on repo url
    const repoInput = getElement("repoUrl");
    if (repoInput) {
        repoInput.addEventListener("keydown", e => {
            if (e.key === "Enter") {
                e.preventDefault();
                analyzeRepository();
            }
        });
    }

    // Impact Analysis Button
    const impactBtn = getElement("analyzeImpactButton");
    if (impactBtn) impactBtn.addEventListener("click", analyzeChangeImpact);

    // Task Guidance Button
    const taskBtn = getElement("taskGuideButton");
    if (taskBtn) taskBtn.addEventListener("click", getTaskGuidance);

    // Generate Guide Button
    const guideBtn = getElement("generateGuideButton");
    if (guideBtn) guideBtn.addEventListener("click", generateOnboardingGuide);

    // Ask Button
    const askBtn = getElement("askButton");
    if (askBtn) askBtn.addEventListener("click", askQuestion);

    // Question input Ctrl+Enter
    const qInput = getElement("questionInput");
    if (qInput) {
        qInput.addEventListener("keydown", e => {
            if (e.key === "Enter" && e.ctrlKey) {
                e.preventDefault();
                askQuestion();
            }
        });
    }

    // Senior Approve Button
    const approveBtn = getElement("seniorApproveButton");
    if (approveBtn) approveBtn.addEventListener("click", approveSeniorReview);
});