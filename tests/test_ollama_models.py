import unittest
from unittest.mock import patch, MagicMock
from core import model

class TestOllamaModel(unittest.TestCase):
    @patch("core.model.subprocess.run")
    def test_get_ollama_models_with_models(self, mock_run):
        # Simulate 'ollama list' output with models
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="NAME            SIZE    MODIFIED\nqwen2.5-coder:1.5b-instruct   4GB   2024-07-01\nother-model   2GB   2024-06-01\n"
        )
        models, error = model.get_ollama_models()
        self.assertIn("qwen2.5-coder:1.5b-instruct", models)
        self.assertIn("other-model", models)
        self.assertIsNone(error)

    @patch("core.model.subprocess.run")
    @patch("builtins.input", return_value="n")
    def test_get_ollama_models_no_models_user_declines(self, mock_input, mock_run):
        # Simulate 'ollama list' output with no models
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="NAME            SIZE    MODIFIED\n"
        )
        models, error = model.get_ollama_models()
        self.assertIsNone(models)
        self.assertIn("No models found", error)

    @patch("core.model.subprocess.run")
    @patch("builtins.input", return_value="y")
    def test_get_ollama_models_no_models_user_accepts(self, mock_input, mock_run):
        # Simulate 'ollama list' output with no models, then simulate successful download
        def side_effect(*args, **kwargs):
            if args[0][:2] == ["ollama", "list"]:
                # First call: no models
                if not hasattr(side_effect, "called"):
                    side_effect.called = True
                    return MagicMock(returncode=0, stdout="NAME            SIZE    MODIFIED\n")
                # Second call: model present
                return MagicMock(returncode=0, stdout="NAME            SIZE    MODIFIED\nqwen2.5-coder:1.5b-instruct   4GB   2024-07-01\n")
            elif args[0][:2] == ["ollama", "run"]:
                return MagicMock(returncode=0, stdout="Model downloaded and ready.")
            return MagicMock(returncode=1, stdout="")

        mock_run.side_effect = side_effect
        models, error = model.get_ollama_models()
        self.assertIn("qwen2.5-coder:1.5b-instruct", models)
        self.assertIsNone(error)

    @patch("core.model.subprocess.run", side_effect=FileNotFoundError())
    def test_get_ollama_models_ollama_not_found(self, mock_run):
        models, error = model.get_ollama_models()
        self.assertIsNone(models)
        self.assertIn("Ollama not found", error)

if __name__ == "__main__":
    unittest.main()