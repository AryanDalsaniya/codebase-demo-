import json
import ollama


# =========================================================
# Configuration
# =========================================================

MODEL_NAME = "llama3.2"
MAX_CONTEXT_LENGTH = 20000


# =========================================================
# Generate Onboarding Guide using Llama 3.2
# =========================================================

def generate_onboarding_guide(project_info):
    """
    Generate a beginner-friendly onboarding guide
    using the analyzed repository information.
    """

    # -----------------------------------------------------
    # Convert project information to JSON
    # -----------------------------------------------------

    try:

        project_json = json.dumps(
            project_info,
            indent=2,
            ensure_ascii=False
        )

    except (TypeError, ValueError) as e:

        print(
            "Could not convert project information to JSON:",
            repr(e)
        )

        return (
            "Could not generate the onboarding guide "
            "because the repository information could "
            "not be processed."
        )

    # -----------------------------------------------------
    # Prevent an excessively large prompt
    # -----------------------------------------------------

    if len(project_json) > MAX_CONTEXT_LENGTH:

        project_json = project_json[:MAX_CONTEXT_LENGTH]

        project_json += (
            "\n\n[Repository information was truncated "
            "because it exceeded the maximum context size.]"
        )

    # -----------------------------------------------------
    # Prompt for Llama 3.2
    # -----------------------------------------------------

    prompt = f"""
You are an expert software engineer helping a new developer
understand an unfamiliar codebase.

The following information was collected directly from
repository analysis:

================ REPOSITORY INFORMATION ================

{project_json}

============== END REPOSITORY INFORMATION ==============

Create a clear and practical onboarding guide for a
developer who has never seen this repository before.

Use exactly these sections:

1. Project Overview
   Explain what the project appears to do based only
   on the repository information.

2. Project Structure
   Explain the important directories and files.

3. Technologies and Languages
   Explain the detected programming languages and
   technologies.

4. Important Files
   Explain which files a new developer should
   understand first.

5. Classes and Functions
   Explain important classes and functions that
   were detected.

6. Dependencies
   Explain the dependencies shown in the repository
   analysis.

7. How to Start Understanding the Project
   Give a practical reading order based only on the
   available repository information.

8. Potential Entry Points
   Identify files or functions that appear to be
   possible entry points.

9. Beginner Notes
   Mention important things a new developer should
   understand or be careful about.

Rules:

1. Use only information contained in the repository
   information above.
2. Do not invent files, classes, functions,
   dependencies, technologies, or behavior.
3. Do not claim that you inspected source code that
   is not included in the repository analysis.
4. Clearly distinguish between detected information
   and things that cannot be determined.
5. If something cannot be determined, write:
   "Could not be determined from the available
   repository information."
6. Use beginner-friendly language.
7. Mention actual file names whenever possible.
8. Keep the guide practical rather than giving
   generic software-development advice.
"""

    # -----------------------------------------------------
    # Call Llama 3.2
    # -----------------------------------------------------

    try:

        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

    except Exception as e:

        print(
            "Ollama error:",
            repr(e)
        )

        return (
            "Could not generate the onboarding guide "
            "using Llama 3.2. Please make sure Ollama "
            "is running and the llama3.2 model is installed."
        )

    # -----------------------------------------------------
    # Validate response
    # -----------------------------------------------------

    if not response:

        return "Llama 3.2 returned an empty response."

    message = response.get("message")

    if not message:

        return (
            "Llama 3.2 returned an unexpected response."
        )

    answer = message.get("content")

    if not answer:

        return (
            "Llama 3.2 returned an empty onboarding guide."
        )

    return answer.strip()