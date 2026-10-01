# Codebase Onboarding Companion

Explore a public GitHub repository without opening every file by hand. The
companion clones and analyzes repositories, displays an overview and file tree,
previews text files, and uses the OpenAI API for an onboarding guide and code
questions.

## Features

- Clone public GitHub repositories, including links copied from branch pages.
- Shallow-clone the default branch to reduce download time and disk usage.
- Summarize languages, files, directories, Python symbols, and common project
  files.
- Browse the repository and preview text files.
- Generate an AI onboarding guide and ask codebase questions with answers linked
  to relevant source files.
- Keep each browser session's cloned repository and analysis separate.

## Requirements

- Python 3.10 or later
- Git installed and available on `PATH`
- An OpenAI API key for the AI guide and Q&A features

Repository analysis and browsing work without an OpenAI key. The key is used by
the backend only; never put it in frontend code, commit it, or share it in chat.
The default model is `gpt-4o-mini`; set `OPENAI_MODEL` to use another model
available to your OpenAI account.

## Run locally on Windows

From the project root, create and activate a virtual environment, then install
the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

In the same terminal, set your API key and start the app:

```powershell
$env:OPENAI_API_KEY = "your-openai-api-key"
$env:APP_PASSWORD = ""
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. The frontend is served by FastAPI from the same
origin. The API documentation is at <http://127.0.0.1:8000/docs>.

To use the separate frontend development server instead, run
`python -m http.server 5500 --directory frontend` and open
<http://127.0.0.1:5500>.

## Deploy on Render

1. Push this repository to GitHub.
2. Sign in at [Render](https://render.com/), choose **New** → **Blueprint**,
   and connect this repository. Render reads [render.yaml](./render.yaml).
3. In the service's **Environment** settings, set `OPENAI_API_KEY` to your
   OpenAI API key and `APP_PASSWORD` to a strong, private access password. Keep
   both values as Render secrets; never put them in this repository. The
   `OPENAI_MODEL` setting defaults to `gpt-4o-mini` and can be changed if needed.
4. Deploy. Render installs `requirements.txt`, starts the FastAPI application,
   and serves the frontend and API from the same URL. Wait for the service to
   finish deploying and report **Live**.

### Access and use the deployed site

1. In the Render dashboard, open the web service and click its `onrender.com`
    URL. This is the public website address to share with users.
2. Paste a public GitHub repository URL into **Bring a repository** and select
    **Analyze repository**. The first protected request prompts for the
    `APP_PASSWORD` you set in Render. Enter it; the browser remembers it for the
    current tab session. Share this password only with people you want to use
    the site.
3. Review the repository overview, then use **File Explorer** to browse the
  tree and preview files.
4. Select **Generate guide** for an AI-written onboarding guide, or ask a
  question in **Codebase Q&A**. Answers include relevant source files.

Repository analysis and file browsing do not require an OpenAI key, but the AI
guide and Q&A do. If those actions report that OpenAI is not configured, check
that `OPENAI_API_KEY` is set in the Render service's environment settings and
redeploy. If you change either secret, redeploy the service for the change to
take effect. A free Render service may take a little while to respond after a
period of inactivity.

The API key never reaches the browser. The optional app password protects the
public site from unauthorized use of your OpenAI account; do not leave it blank
on a publicly shared deployment. OpenAI API usage may incur charges according
to your OpenAI account's billing.

### Hosting limitations

Repository clones and per-browser-session analysis are kept under `data/`.
Render's default filesystem is temporary: deployments, restarts, or instance
replacement can clear this data, so users may need to analyze a repository
again. This is a single-instance demo deployment, not a durable multi-instance
service. Add persistent storage and coordinated session storage before scaling
to multiple instances.

## Run tests

```powershell
python -m unittest discover -s tests -v
```

## Notes

- Only public GitHub repositories are supported; only the default branch is
  cloned.
- Common generated folders such as `node_modules`, virtual environments, build
  outputs, and `.git` are skipped during analysis.
- `OPENAI_API_KEY` and `APP_PASSWORD` are read from server environment
  variables. Do not commit actual secret values.
