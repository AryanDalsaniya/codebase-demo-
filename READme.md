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
- Generate an onboarding guide and ask codebase questions with OpenAI.
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
3. Set `OPENAI_API_KEY` in the service's environment settings to your key. Set
   `APP_PASSWORD` to a strong, private password before sharing the site. Keep
   both values as Render secrets; do not put them in this repository.
4. Deploy. Render installs `requirements.txt`, starts the FastAPI application,
   and serves both the frontend and API from the same URL.
5. Open the `onrender.com` URL from the service page, enter the app password
   when prompted, and analyze a public GitHub repository.

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
