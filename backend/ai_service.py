import logging
import os

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.5-flash"


def generate_ai_response(prompt: str) -> str:
    """
    Generate an AI response using the Google Gemini API.
    Supports either GEMINI_API_KEY or GOOGLE_API_KEY.
    Uses the official google-genai SDK with an automatic HTTP REST fallback.
    """
    api_key = (
        os.environ.get("GEMINI_API_KEY", "").strip()
        or os.environ.get("GOOGLE_API_KEY", "").strip()
    )
    if not api_key:
        raise RuntimeError(
            "Google Gemini API is not configured. Set the GEMINI_API_KEY or GOOGLE_API_KEY environment variable."
        )

    model = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL

    # Primary method: official google-genai SDK
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )
        if response and getattr(response, "text", None):
            return response.text.strip()
    except Exception as sdk_error:
        logger.warning(
            "google-genai SDK call failed or unavailable (%s), trying HTTP REST fallback...",
            sdk_error,
        )

    # Resilient fallback: direct Gemini REST API via httpx
    try:
        import httpx

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }
        headers = {"Content-Type": "application/json"}

        with httpx.Client(timeout=60.0) as http_client:
            res = http_client.post(
                url,
                params={"key": api_key},
                json=payload,
                headers=headers,
            )
            res.raise_for_status()
            data = res.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts and "text" in parts[0]:
                    return parts[0]["text"].strip()
    except Exception as rest_error:
        logger.error("Gemini REST API fallback error: %s", rest_error)
        raise RuntimeError(
            f"Failed to generate response from Google Gemini: {rest_error}"
        ) from rest_error

    raise RuntimeError("The Google Gemini API returned an empty response.")
