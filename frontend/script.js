"use strict";


/*
=========================================================
CODEBASE ONBOARDING COMPANION
=========================================================

Frontend
   ↓
FastAPI
   ↓
Repository Analyzer
   ↓
project_info.json

Q&A:

Frontend
   ↓
/ask
   ↓
code_search.py
   ↓
Relevant repository code
   ↓
Llama 3.2
   ↓
Answer
=========================================================
*/


const API_BASE = "http://127.0.0.1:8000";


/* ========================================================
   DOM HELPER
======================================================== */

function getElement(id) {

    return document.getElementById(id);

}


/* ========================================================
   SHOW / HIDE
======================================================== */

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


/* ========================================================
   SET TEXT
======================================================== */

function setText(id, value) {

    const element = getElement(id);

    if (!element) {
        return;
    }

    if (
        value === undefined ||
        value === null ||
        value === ""
    ) {

        element.textContent = "—";

    }
    else {

        element.textContent = String(value);

    }

}


/* ========================================================
   GENERAL ERROR
======================================================== */

function showError(message) {

    const error = getElement("error");

    if (!error) {
        return;
    }

    error.textContent = message;

    show(error);

}


function clearError() {

    const error = getElement("error");

    if (!error) {
        return;
    }

    error.textContent = "";

    hide(error);

}


/* ========================================================
   API REQUEST
======================================================== */

async function apiRequest(
    endpoint,
    options = {}
) {

    const response = await fetch(
        API_BASE + endpoint,
        options
    );


    let data;

    try {

        data = await response.json();

    }
    catch {

        throw new Error(
            `Backend returned an invalid response (${response.status}).`
        );

    }


    if (!response.ok) {

        throw new Error(
            data.detail ||
            data.error ||
            data.message ||
            `Request failed with status ${response.status}.`
        );

    }


    return data;

}


/* ========================================================
   ANALYZE REPOSITORY
======================================================== */

async function analyzeRepository() {

    const repoInput =
        getElement("repoUrl");

    const analyzeButton =
        getElement("analyzeButton");

    const loading =
        getElement("loading");

    const result =
        getElement("result");


    const repoUrl =
        repoInput
            ? repoInput.value.trim()
            : "";


    if (!repoUrl) {

        showError(
            "Please enter a GitHub repository URL."
        );

        return;

    }


    clearError();

    hide(result);

    show(loading);


    if (analyzeButton) {
        analyzeButton.disabled = true;
    }


    console.log(
        "Starting repository analysis..."
    );


    try {

        /*
        ==================================================
        STEP 1
        ANALYZE REPOSITORY
        ==================================================
        */

        const analyzeData =
            await apiRequest(
                "/analyze",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        repo_url: repoUrl
                    })
                }
            );


        console.log(
            "Analyze response:",
            analyzeData
        );


        /*
        ==================================================
        STEP 2
        GET SUMMARY
        ==================================================
        */

        const summaryData =
            await apiRequest(
                "/summary"
            );


        console.log(
            "Summary:",
            summaryData
        );


        displaySummary(
            summaryData
        );


        /*
        ==================================================
        STEP 3
        FILE TREE
        ==================================================
        */

        await loadRepositoryFileTree();


        /*
        ==================================================
        STEP 4
        SHOW RESULTS
        ==================================================
        */

        show(result);


        /*
        ==================================================
        STEP 5
        GENERATE AI GUIDE
        ==================================================
        */

        await generateOnboardingGuide();


        console.log(
            "Repository analysis completed."
        );

    }
    catch (error) {

        console.error(
            "Analysis error:",
            error
        );


        showError(
            error.message ||
            "Could not analyze the repository."
        );

    }
    finally {

        hide(loading);


        if (analyzeButton) {
            analyzeButton.disabled = false;
        }

    }

}


/* ========================================================
   DISPLAY SUMMARY
======================================================== */

function displaySummary(summary) {

    if (!summary) {
        return;
    }


    /*
    ==================================================
    PROJECT
    ==================================================
    */

    setText(
        "projectName",
        summary.project_name ||
        "Unknown"
    );


    /*
    ==================================================
    STATISTICS
    ==================================================
    */

    const statistics =
        summary.statistics || {};


    setText(
        "fileCount",
        statistics.files ?? 0
    );


    setText(
        "directoryCount",
        statistics.directories ?? 0
    );


    /*
    ==================================================
    LANGUAGES
    ==================================================
    */

    const languages =
        summary.languages || {};


    const languageNames =
        Object.keys(languages);


    setText(
        "languageCount",
        languageNames.length
    );


    displayLanguages(
        languages
    );


    /*
    ==================================================
    PYTHON ANALYSIS
    ==================================================
    */

    const pythonAnalysis =
        summary.python_analysis || {};


    const classes =
        pythonAnalysis.classes ||
        summary.classes ||
        [];


    const functions =
        pythonAnalysis.functions ||
        summary.functions ||
        [];


    setText(
        "classCount",
        Array.isArray(classes)
            ? classes.length
            : classes
    );


    setText(
        "functionCount",
        Array.isArray(functions)
            ? functions.length
            : functions
    );


    /*
    ==================================================
    IMPORTANT FILES
    ==================================================
    */

    displayImportantFiles(
        summary.important_files || []
    );


    /*
    ==================================================
    DEPENDENCIES
    ==================================================
    */

    displayDependencies(
        summary.dependencies || {}
    );


    /*
    ==================================================
    DESCRIPTION
    ==================================================
    */

    const description =
        summary.description ||
        summary.project_description ||
        "";


    const readme =
        summary.readme ||
        "";


    const descriptionElement =
        getElement(
            "projectDescription"
        );


    if (!descriptionElement) {
        return;
    }


    if (description) {

        descriptionElement.textContent =
            description;

    }
    else if (readme) {

        descriptionElement.textContent =
            readme.length > 1500
                ? readme.substring(0, 1500) + "..."
                : readme;

    }
    else {

        descriptionElement.textContent =
            "Repository analyzed successfully.";

    }

}


/* ========================================================
   LANGUAGES
======================================================== */

function displayLanguages(languages) {

    const container =
        getElement("languages");


    if (!container) {
        return;
    }


    container.innerHTML = "";


    const names =
        Object.keys(
            languages || {}
        );


    if (names.length === 0) {

        container.innerHTML =
            `
            <span class="language-tag">
                No language information available
            </span>
            `;

        return;
    }


    names.forEach(language => {

        const tag =
            document.createElement(
                "span"
            );


        tag.className =
            "language-tag";


        const value =
            languages[language];


        if (
            typeof value === "number"
        ) {

            tag.textContent =
                `${language} (${value})`;

        }
        else {

            tag.textContent =
                language;

        }


        container.appendChild(
            tag
        );

    });

}


/* ========================================================
   DEPENDENCIES
======================================================== */

function displayDependencies(
    dependencies
) {

    const container =
        getElement(
            "dependencies"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    /*
    ==================================================
    PYTHON REQUIREMENTS
    ==================================================
    */

    const requirements =
        dependencies.python_requirements ||
        [];


    if (
        Array.isArray(requirements) &&
        requirements.length > 0
    ) {

        requirements.forEach(
            requirement => {

                const element =
                    document.createElement(
                        "div"
                    );


                element.className =
                    "dependency-item";


                element.textContent =
                    requirement;


                container.appendChild(
                    element
                );

            }
        );


        return;
    }


    /*
    ==================================================
    OTHER DEPENDENCY FORMATS
    ==================================================
    */

    const dependencyValues =
        Object.values(
            dependencies
        );


    let found = false;


    dependencyValues.forEach(
        dependencyGroup => {

            if (
                Array.isArray(
                    dependencyGroup
                )
            ) {

                dependencyGroup.forEach(
                    dependency => {

                        const element =
                            document.createElement(
                                "div"
                            );


                        element.className =
                            "dependency-item";


                        element.textContent =
                            dependency;


                        container.appendChild(
                            element
                        );


                        found = true;

                    }
                );

            }

        }
    );


    if (!found) {

        container.textContent =
            "No dependencies detected.";

    }

}


/* ========================================================
   IMPORTANT FILES
======================================================== */

function displayImportantFiles(
    files
) {

    const container =
        getElement(
            "importantFiles"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (
        !Array.isArray(files) ||
        files.length === 0
    ) {

        container.innerHTML =
            `
            <div class="important-file">
                No important files detected.
            </div>
            `;

        return;
    }


    files.forEach(file => {

        let fileName = file;


        if (
            typeof file === "object"
        ) {

            fileName =
                file.path ||
                file.file ||
                file.name ||
                "Unknown file";

        }


        const element =
            document.createElement(
                "div"
            );


        element.className =
            "important-file";


        element.textContent =
            fileName;


        element.addEventListener(
            "click",
            () => {

                loadFile(
                    fileName
                );

            }
        );


        container.appendChild(
            element
        );

    });

}


/* ========================================================
   LOAD FILE TREE
======================================================== */

async function loadRepositoryFileTree() {

    const container =
        getElement(
            "fileTree"
        );


    if (!container) {
        return;
    }


    container.innerHTML =
        "Loading files...";


    try {

        const data =
            await apiRequest(
                "/file-tree"
            );


        console.log(
            "File tree:",
            data
        );


        const tree =
            data.file_tree ||
            data.tree ||
            data.files ||
            [];


        container.innerHTML = "";


        if (
            !Array.isArray(tree) ||
            tree.length === 0
        ) {

            container.textContent =
                "No files found.";

            return;
        }


        renderFileTree(
            tree,
            container
        );

    }
    catch (error) {

        console.error(
            "File tree error:",
            error
        );


        container.textContent =
            "Could not load file tree.";

    }

}


/* ========================================================
   RENDER FILE TREE
======================================================== */

function renderFileTree(
    items,
    container,
    parentPath = ""
) {

    if (
        !Array.isArray(items)
    ) {

        return;

    }


    items.forEach(item => {

        if (!item) {
            return;
        }


        const name =
            item.name ||
            item.path ||
            "Unknown";


        const currentPath =
            parentPath
                ? `${parentPath}/${name}`
                : name;


        /*
        ==================================================
        DIRECTORY
        ==================================================
        */

        if (
            item.type === "directory" ||
            item.type === "folder" ||
            Array.isArray(item.children)
        ) {

            const wrapper =
                document.createElement(
                    "div"
                );


            const directory =
                document.createElement(
                    "div"
                );


            directory.className =
                "tree-item tree-directory";


            directory.textContent =
                `📁 ${name}`;


            wrapper.appendChild(
                directory
            );


            const children =
                document.createElement(
                    "div"
                );


            children.className =
                "tree-children";


            renderFileTree(
                item.children || [],
                children,
                currentPath
            );


            wrapper.appendChild(
                children
            );


            directory.addEventListener(
                "click",
                () => {

                    if (
                        children.style.display ===
                        "none"
                    ) {

                        children.style.display =
                            "block";

                    }
                    else {

                        children.style.display =
                            "none";

                    }

                }
            );


            container.appendChild(
                wrapper
            );

        }


        /*
        ==================================================
        FILE
        ==================================================
        */

        else {

            const file =
                document.createElement(
                    "div"
                );


            file.className =
                "tree-item tree-file";


            file.textContent =
                `📄 ${name}`;


            file.addEventListener(
                "click",
                () => {

                    loadFile(
                        currentPath
                    );

                }
            );


            container.appendChild(
                file
            );

        }

    });

}


/* ========================================================
   LOAD FILE
======================================================== */

async function loadFile(
    filePath
) {

    const contentElement =
        getElement(
            "fileContent"
        );


    const pathElement =
        getElement(
            "filePath"
        );


    if (!contentElement) {
        return;
    }


    if (!filePath) {

        contentElement.textContent =
            "No file selected.";

        return;
    }


    contentElement.textContent =
        "Loading file...";


    if (pathElement) {

        pathElement.textContent =
            filePath;

    }


    try {

        const encodedPath =
            encodeURIComponent(
                filePath
            );


        const data =
            await apiRequest(
                `/file?path=${encodedPath}`
            );


        const content =
            data.content ??
            data.file_content ??
            data.text ??
            "";


        contentElement.textContent =
            content ||
            "This file is empty.";

    }
    catch (error) {

        console.error(
            "File error:",
            error
        );


        contentElement.textContent =
            `Could not load file.\n\n${error.message}`;

    }

}


/* ========================================================
   GENERATE ONBOARDING GUIDE
======================================================== */

async function generateOnboardingGuide() {

    const button =
        getElement(
            "generateGuideButton"
        );


    const loading =
        getElement(
            "guideLoading"
        );


    const error =
        getElement(
            "guideError"
        );


    const guide =
        getElement(
            "onboardingGuide"
        );


    hide(error);

    hide(guide);

    show(loading);


    if (button) {
        button.disabled = true;
    }


    try {

        console.log(
            "Generating onboarding guide..."
        );


        const data =
            await apiRequest(
                "/onboarding-guide"
            );


        console.log(
            "Onboarding guide:",
            data
        );


        const guideText =
            data.guide ||
            data.onboarding_guide ||
            data.content ||
            data.message ||
            "";


        if (!guideText) {

            throw new Error(
                "The onboarding guide was empty."
            );

        }


        guide.textContent =
            guideText;


        show(guide);

    }
    catch (errorObject) {

        console.error(
            "Guide error:",
            errorObject
        );


        if (error) {

            error.textContent =
                errorObject.message ||
                "Could not generate the onboarding guide.";


            show(error);

        }

    }
    finally {

        hide(loading);


        if (button) {
            button.disabled = false;
        }

    }

}


/* ========================================================
   ASK QUESTION
======================================================== */

async function askQuestion() {

    const input =
        getElement(
            "questionInput"
        );


    const button =
        getElement(
            "askButton"
        );


    const loading =
        getElement(
            "qaLoading"
        );


    const error =
        getElement(
            "qaError"
        );


    const answerBox =
        getElement(
            "qaAnswer"
        );


    const answerText =
        getElement(
            "answerText"
        );


    const answerSources =
        getElement(
            "answerSources"
        );


    const question =
        input
            ? input.value.trim()
            : "";


    if (!question) {

        if (error) {

            error.textContent =
                "Please enter a question.";

            show(error);

        }

        return;

    }


    hide(error);

    hide(answerBox);

    show(loading);


    if (button) {
        button.disabled = true;
    }


    try {

        console.log(
            "Question:",
            question
        );


        const data =
            await apiRequest(
                "/ask",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        question: question
                    })
                }
            );


        console.log(
            "Q&A response:",
            data
        );


        /*
        ================================================
        ANSWER
        ================================================
        */

        const answer =
            data.answer ||
            data.response ||
            data.message ||
            "";


        if (answerText) {

            answerText.textContent =
                answer ||
                "No answer was returned.";

        }


        /*
        ================================================
        SOURCES
        ================================================
        */

        displayAnswerSources(
            data.sources || []
        );


        show(answerBox);

    }
    catch (errorObject) {

        console.error(
            "Q&A error:",
            errorObject
        );


        if (error) {

            error.textContent =
                errorObject.message ||
                "Could not answer the question.";

            show(error);

        }

    }
    finally {

        hide(loading);


        if (button) {
            button.disabled = false;
        }

    }

}


/* ========================================================
   ANSWER SOURCES
======================================================== */

function displayAnswerSources(
    sources
) {

    const container =
        getElement(
            "answerSources"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (
        !Array.isArray(sources) ||
        sources.length === 0
    ) {

        container.innerHTML =
            `
            <div class="source-item">
                No source information returned.
            </div>
            `;

        return;
    }


    sources.forEach(source => {

        const element =
            document.createElement(
                "div"
            );


        element.className =
            "source-item";


        if (
            typeof source === "string"
        ) {

            element.textContent =
                source;

        }
        else {

            const file =
                source.file ||
                source.path ||
                "Unknown file";


            const line =
                source.line ||
                source.line_number ||
                "";


            element.textContent =
                line
                    ? `${file} — line ${line}`
                    : file;

        }


        container.appendChild(
            element
        );

    });

}


/* ========================================================
   QUESTION INPUT
======================================================== */

function setupQuestionInput() {

    const input =
        getElement(
            "questionInput"
        );


    if (!input) {
        return;
    }


    input.addEventListener(
        "keydown",
        event => {

            /*
            Ctrl + Enter
            sends the question
            */

            if (
                event.key === "Enter" &&
                event.ctrlKey
            ) {

                event.preventDefault();

                askQuestion();

            }

        }
    );

}


/* ========================================================
   ENTER KEY FOR REPOSITORY URL
======================================================== */

function setupRepositoryInput() {

    const input =
        getElement(
            "repoUrl"
        );


    if (!input) {
        return;
    }


    input.addEventListener(
        "keydown",
        event => {

            if (
                event.key === "Enter"
            ) {

                event.preventDefault();

                analyzeRepository();

            }

        }
    );

}


/* ========================================================
   INITIALIZE
======================================================== */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        console.log(
            "Codebase Onboarding Companion loaded."
        );


        /*
        ================================================
        ANALYZE BUTTON
        ================================================
        */

        const analyzeButton =
            getElement(
                "analyzeButton"
            );


        if (analyzeButton) {

            analyzeButton.addEventListener(
                "click",
                analyzeRepository
            );

        }


        /*
        ================================================
        AI GUIDE BUTTON
        ================================================
        */

        const guideButton =
            getElement(
                "generateGuideButton"
            );


        if (guideButton) {

            guideButton.addEventListener(
                "click",
                generateOnboardingGuide
            );

        }


        /*
        ================================================
        ASK BUTTON
        ================================================
        */

        const askButton =
            getElement(
                "askButton"
            );


        if (askButton) {

            askButton.addEventListener(
                "click",
                askQuestion
            );

        }


        /*
        ================================================
        INPUTS
        ================================================
        */

        setupQuestionInput();

        setupRepositoryInput();

    }
);