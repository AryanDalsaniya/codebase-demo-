# Codebase Onboarding Companion

Understand an unfamiliar GitHub codebase from one page. Paste a public
repository link to see its structure, identify key files, preview source code,
and get an optional AI-generated onboarding guide or answers to code questions.

## What You Get

After analysis, the page shows:

- A repository overview with the project name, file and directory counts,
  detected languages, and Python class/function counts.
- Detected dependencies and a list of important project files.
- A file explorer with previews of supported text files.
- An AI onboarding guide for a high-level explanation of the project.
- Codebase Q&A answers with links to relevant source files.

The overview and file explorer work without an OpenAI API key. The AI guide and
Q&A require one.

## Open the App

### Use the deployed website

If the project has been deployed to Render, open the Render dashboard, select
the web service, and click its public `onrender.com` URL. That URL is the
website; you do not need to run the code on your computer. If the site owner
configured `APP_PASSWORD`, enter that password when the app prompts you. It is
remembered for the current browser tab session.

### Run it on your computer

Install Python 3.10 or later and Git, then open a terminal in the project root
(the folder containing `requirements.txt`). On Windows PowerShell, install the
dependencies and start the web app:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

To enable the AI guide and Q&A locally, set your OpenAI key in the same
PowerShell window. Skip this step if you only need repository analysis and file
browsing:

```powershell
$env:OPENAI_API_KEY = "your-openai-api-key"
```

Start the app from the project root:

```powershell
$env:APP_PASSWORD = ""
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000> in your browser. Keep the terminal running while
you use the app. The API key stays on the server; never put a real key in
frontend files or commit it to GitHub. The app uses `gpt-4o-mini` by default.
Set `OPENAI_MODEL` to another model available to your account if needed.

## Analyze a Repository

1. Open the deployed website or the local address above.
2. Paste a public GitHub repository URL into **Bring a repository**. Links
   copied from a branch page are accepted too.
3. Select **Analyze repository** and wait for the overview to appear.
4. Explore the summary, dependencies, important files, and **File Explorer**.
   Select a file in the tree to preview its contents.
5. Select **Generate guide** for an AI onboarding guide, or ask a question in
   **Codebase Q&A**. Answers show their relevant source files.

Only public repositories are supported, and the app analyzes the repository's
default branch. Each browser session keeps its own analysis. Large repositories
may take longer to clone and analyze.

## Deploy on Render

1. Push this project to GitHub.
2. In [Render](https://render.com/), choose **New** → **Blueprint** and connect
   the GitHub repository. Render uses [render.yaml](./render.yaml) to configure
   the web service.
3. In the service's environment settings, set `OPENAI_API_KEY` for AI features
   and set `APP_PASSWORD` to a strong password before sharing the site. Keep
   both values private; do not commit them to the repository.
4. Deploy and wait for the service status to show **Live**. In the Render
   dashboard, open the service and click its public `onrender.com` URL to use
   the app.

OpenAI API usage may incur charges. On Render's free plan, the service may take
a little while to respond after inactivity. Repository clones and analysis
data are temporary and may be cleared when the service restarts or is replaced.

## Technologies

- Frontend: HTML, CSS, and JavaScript.
- Backend: Python and FastAPI.
- Repository cloning: GitPython and Git.
- AI guide and code answers: OpenAI API.

## Run Tests

```powershell
python -m unittest discover -s tests -v
```
