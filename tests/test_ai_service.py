import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.ai_service import generate_ai_response


class GenerateAiResponseTests(unittest.TestCase):
    def test_requires_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY"):
                generate_ai_response("test prompt")

    @patch("backend.ai_service.OpenAI")
    def test_uses_configured_model_and_returns_text(self, openai_class):
        message = SimpleNamespace(content="  A useful answer.  ")
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=message)]
        )
        openai_class.return_value.chat.completions.create.return_value = response

        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "OPENAI_MODEL": "test-model",
            },
        ):
            answer = generate_ai_response("test prompt")

        self.assertEqual(answer, "A useful answer.")
        openai_class.assert_called_once_with(
            api_key="test-key",
            timeout=60.0,
            max_retries=2,
        )
        openai_class.return_value.chat.completions.create.assert_called_once_with(
            model="test-model",
            messages=[{"role": "user", "content": "test prompt"}],
        )


if __name__ == "__main__":
    unittest.main()
