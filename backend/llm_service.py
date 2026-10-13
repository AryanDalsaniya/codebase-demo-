import json

from backend.ai_service import generate_ai_response


MAX_CONTEXT_LENGTH = 20000


def generate_onboarding_guide(project_info):
    """Generate a beginner-friendly guide from analyzed repository metadata."""

    try:
        project_json = json.dumps(
            project_info,
            indent=2,
            ensure_ascii=False,
        )
    except (TypeError, ValueError) as error:
        raise RuntimeError(
            "Repository information could not be processed for the AI guide."
        ) from error

    if len(project_json) > MAX_CONTEXT_LENGTH:
        project_json = project_json[:MAX_CONTEXT_LENGTH]
        project_json += (
            "\n\n[Repository information was truncated because it exceeded "
            "the maximum context size.]"
        )

    prompt = f"""
You are an expert software engineer helping a new developer understand an
unfamiliar codebase.

The following information was collected directly from repository analysis:

================ REPOSITORY INFORMATION ================

{project_json}

============== END REPOSITORY INFORMATION ==============

Create a clear and practical onboarding guide for a developer who has never
seen this repository before. Use exactly these sections:

1. Project Overview
2. Project Structure
3. Technologies and Languages
4. Important Files
5. Classes and Functions
6. Dependencies
7. How to Start Understanding the Project
8. Potential Entry Points
9. Beginner Notes

Use only the repository information above. Do not invent files, classes,
functions, dependencies, technologies, or behavior. Clearly identify anything
that cannot be determined from the available repository information. Use
beginner-friendly language, mention actual filenames, and keep the guide
practical.
"""

    return generate_ai_response(prompt)
