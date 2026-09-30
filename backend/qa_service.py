import ollama


# =========================================================
# Generate Codebase Answer
# =========================================================

def generate_codebase_answer(question, search_results):

    # -----------------------------------------------------
    # No search results
    # -----------------------------------------------------

    if not search_results:

        return (
            "I could not find relevant code in the repository "
            "to answer this question."
        )

    # -----------------------------------------------------
    # Build repository context
    # -----------------------------------------------------

    context_parts = []

    for result in search_results:

        file_name = result.get("file", "Unknown file")
        line_number = result.get("line", "Unknown")
        content = result.get("content", "")

        context_parts.append(
            f"""
File: {file_name}
Line: {line_number}

Relevant Code:
{content}
"""
        )

    context = "\n".join(context_parts)

    # -----------------------------------------------------
    # Limit context size
    # -----------------------------------------------------

    # Prevent extremely large prompts from being sent
    # to the local Llama model.
    max_context_length = 12000

    if len(context) > max_context_length:

        context = context[:max_context_length]

        context += (
            "\n\n[Additional search results were omitted "
            "because the context became too large.]"
        )

    # -----------------------------------------------------
    # Prompt for Llama 3.2
    # -----------------------------------------------------

    prompt = f"""
You are an expert software engineer helping a new developer
understand an unfamiliar codebase.

The developer asked:

{question}

The following information was retrieved directly from
the repository:

---------------- REPOSITORY CONTEXT ----------------

{context}

---------------- END REPOSITORY CONTEXT --------------

Answer the developer's question using ONLY the repository
information provided above.

Rules:

1. Answer the question directly.
2. Use simple, beginner-friendly language.
3. Mention relevant file names.
4. Mention line numbers when useful.
5. Explain relevant classes, functions, variables,
   or logic when they appear in the provided code.
6. Do not invent code, files, classes, functions,
   dependencies, or behavior.
7. Do not assume functionality that is not shown.
8. Clearly distinguish what can be determined from
   the provided repository context.
9. If the provided context is insufficient, say:
   "The retrieved repository code is not sufficient
   to determine this."
10. Do not claim that you inspected files that were
    not included in the repository context.
11. Keep the answer focused on the developer's question.
12. When possible, explain the answer step-by-step.

Return a practical explanation for a developer who is
new to this codebase.
"""

    # -----------------------------------------------------
    # Call Llama 3.2 through Ollama
    # -----------------------------------------------------

    try:

        response = ollama.chat(
            model="llama3.2",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # -------------------------------------------------
        # Extract response safely
        # -------------------------------------------------

        if not response:
            return "Llama did not return an answer."

        message = response.get("message")

        if not message:
            return "Llama returned an unexpected response."

        answer = message.get("content")

        if not answer:
            return "Llama returned an empty answer."

        return answer.strip()

    except Exception as e:

        print(
            "Llama error:",
            repr(e)
        )

        return (
            "Could not generate an answer using "
            "Llama 3.2. Please make sure Ollama is "
            "running and the llama3.2 model is available."
        )