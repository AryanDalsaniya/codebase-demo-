import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from backend.ai_service import generate_ai_response


class GenerateAiResponseTests(unittest.TestCase):
    def test_requires_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "GEMINI_API_KEY"):
                generate_ai_response("test prompt")

    @patch("google.genai.Client")
    def test_uses_gemini_sdk_and_returns_text(self, mock_client_cls):
        mock_client = MagicMock()
        mock_response = SimpleNamespace(text="  A clear Gemini explanation.  ")
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with patch.dict(
            os.environ,
            {
                "GEMINI_API_KEY": "test-gemini-key",
                "GEMINI_MODEL": "gemini-2.5-flash",
            },
            clear=True,
        ):
            answer = generate_ai_response("Explain this code")

        self.assertEqual(answer, "A clear Gemini explanation.")
        mock_client_cls.assert_called_once_with(api_key="test-gemini-key")
        mock_client.models.generate_content.assert_called_once_with(
            model="gemini-2.5-flash",
            contents="Explain this code",
        )

    @patch("google.genai.Client")
    def test_accepts_google_api_key_environment_variable(self, mock_client_cls):
        mock_client = MagicMock()
        mock_response = SimpleNamespace(text="Answer with GOOGLE_API_KEY")
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with patch.dict(
            os.environ,
            {
                "GOOGLE_API_KEY": "test-google-key",
            },
            clear=True,
        ):
            answer = generate_ai_response("Explain this code")

        self.assertEqual(answer, "Answer with GOOGLE_API_KEY")
        mock_client_cls.assert_called_once_with(api_key="test-google-key")

    @patch("httpx.Client")
    @patch("google.genai.Client", side_effect=Exception("SDK failure"))
    def test_http_rest_fallback_on_sdk_error(self, mock_genai, mock_httpx_cls):
        mock_http_instance = MagicMock()
        mock_http_response = MagicMock()
        mock_http_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Fallback REST response text"}
                        ]
                    }
                }
            ]
        }
        mock_http_response.raise_for_status = MagicMock()
        mock_http_instance.post.return_value = mock_http_response
        mock_httpx_cls.return_value.__enter__.return_value = mock_http_instance

        with patch.dict(
            os.environ,
            {
                "GEMINI_API_KEY": "test-gemini-key",
            },
            clear=True,
        ):
            answer = generate_ai_response("Explain this code")

        self.assertEqual(answer, "Fallback REST response text")


if __name__ == "__main__":
    unittest.main()
