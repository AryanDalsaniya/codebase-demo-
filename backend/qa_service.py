from backend.ai_service import generate_ai_response


MAX_CONTEXT_LENGTH = 12000


def generate_codebase_answer(question, search_results):
    if not search_results:
        return (
            "I could not find relevant code in the repository "
            "to answer this question."
        )

    context_parts = []
    for result in search_results:
        context_parts.append(
            f"File: {result.get('file', 'Unknown file')}\n"
            f"Line: {result.get('line', 'Unknown')}\n"
            f"Relevant code:\n{result.get('content', '')}"
        )

    context = "\n\n".join(context_parts)
    if len(context) > MAX_CONTEXT_LENGTH:
        context = context[:MAX_CONTEXT_LENGTH] + (
            "\n\n[Additional search results were omitted because the context "
            "became too large.]"
        )

    prompt = f"""
You are an expert software engineer helping a new developer understand an
unfamiliar codebase.

The developer asked:
{question}

The following information was retrieved directly from the repository:

---------------- REPOSITORY CONTEXT ----------------
{context}
---------------- END REPOSITORY CONTEXT ------------

Answer using only the repository information above. Be direct and beginner
friendly. Mention relevant files and line numbers when useful. Do not invent
code, files, dependencies, or behavior, and do not claim to have inspected
files not shown here. If the context is insufficient, say:
"The retrieved repository code is not sufficient to determine this."
"""

    return generate_ai_response(prompt)
