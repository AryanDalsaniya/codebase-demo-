import os

from openai import OpenAI


DEFAULT_MODEL = "gpt-4o-mini"


def generate_ai_response(prompt):
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "OpenAI is not configured. Set the OPENAI_API_KEY environment variable."
        )

    model = os.environ.get("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    client = OpenAI(api_key=api_key, timeout=60.0, max_retries=2)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )

    if not response.choices or not response.choices[0].message.content:
        raise RuntimeError("The AI provider returned an empty response.")

    return response.choices[0].message.content.strip()
