import os

# =========================================================
# Generate Codebase Answer
# =========================================================

def generate_codebase_answer(question, search_results, conversation_history=None):
    """
    FR-05: Codebase Question-Answering with conversational context retention.
    FR-06 & US-SD-01: Source-Referenced Answers grounded in actual code.
    If no source can be cited, states it cannot answer confidently.
    """

    # -----------------------------------------------------
    # US-SD-01 & NFR-02 Safeguard: No search results found
    # -----------------------------------------------------

    if not search_results:
        return (
            "I cannot find sufficient evidence in the repository code to answer "
            "this question with confidence. To ensure accuracy and avoid hallucinations, "
            "unverified answers are not generated. Please check the Codebase Map or explore "
            "relevant files directly in the File Explorer."
        )

    # -----------------------------------------------------
    # Build repository context (excluding sensitive files)
    # -----------------------------------------------------

    context_parts = []

    for result in search_results:
        file_name = result.get("file", "Unknown file")
        line_number = result.get("line", "Unknown")
        content = result.get("content", "")

        context_parts.append(
            f"File: {file_name}\nLine: {line_number}\nRelevant Code:\n{content}\n"
        )

    context = "\n".join(context_parts)

    # -----------------------------------------------------
    # Format conversational history (FR-05)
    # -----------------------------------------------------

    history_str = ""
    if conversation_history and isinstance(conversation_history, list):
        recent_turns = conversation_history[-4:]
        lines = []
        for turn in recent_turns:
            role = turn.get("role", "user").capitalize()
            text = turn.get("content", "")
            if text:
                lines.append(f"{role}: {text}")
        if lines:
            history_str = "Prior Conversation Context:\n" + "\n".join(lines) + "\n\n"

    # -----------------------------------------------------
    # Limit context size
    # -----------------------------------------------------

    max_context_length = 12000

    if len(context) > max_context_length:
        context = context[:max_context_length]
        context += (
            "\n\n[Additional search results were omitted "
            "because the context reached the maximum safe window.]"
        )

    # -----------------------------------------------------
    # Prompt for AI model
    # -----------------------------------------------------

    prompt = f"""
You are an expert software engineer helping a junior developer understand an unfamiliar codebase.

{history_str}Current Question:
{question}

---------------- REPOSITORY CONTEXT ----------------
{context}
---------------- END REPOSITORY CONTEXT --------------

Answer the developer's question using ONLY the repository information provided above.

Requirements:
1. Answer the question directly and concisely in plain, beginner-friendly language.
2. Every explanation must cite its source using the exact format `[file_name:line]` (e.g., `[main.cpp:12]`).
3. Explain relevant classes, functions, or logic when they appear in the provided code.
4. Do not invent code, files, classes, functions, or behavior.
5. If the provided context is insufficient, explicitly state:
   "The retrieved repository code is not sufficient to determine this."
6. Never show an ungrounded or fabricated answer.
"""

    # -----------------------------------------------------
    # Call AI Provider (OpenAI if configured, Ollama fallback)
    # -----------------------------------------------------

    if os.environ.get("OPENAI_API_KEY", "").strip():
        from backend.ai_service import generate_ai_response
        return generate_ai_response(prompt)

    try:
        import ollama
        response = ollama.chat(
            model=os.environ.get("OLLAMA_MODEL", "llama3.2"),
            messages=[{"role": "user", "content": prompt}]
        )
        if response and response.get("message", {}).get("content"):
            return response["message"]["content"].strip()
    except Exception as e:
        print("Ollama error:", repr(e))

    from backend.ai_service import generate_ai_response
    return generate_ai_response(prompt)