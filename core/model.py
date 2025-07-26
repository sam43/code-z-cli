# core/model.py
import subprocess
import re

OLLAMA_GITHUB_URL = "https://github.com/ollama/ollama"
DEFAULT_MODEL = "qwen2.5-coder:1.5b-instruct"

def query_ollama(prompt: str, model: str = DEFAULT_MODEL):
    """
    Query the Ollama LLM with the given prompt and model.
    You can change the model at any time using the /models or /model command in the CLI.
    """
    result = subprocess.run(
        ["ollama", "run", model, prompt],
        capture_output=True,
        text=True
    )
    # Optionally, strip markdown formatting from code blocks for terminal display
    output = result.stdout.strip()
    # Remove markdown headers and excessive formatting
    output = re.sub(r'#.*\n', '', output)
    return output

def get_ollama_models():
    """
    Returns a tuple: (list_of_models, error_message)
    If no models are found, prompts the user to download the default model.
    """
    try:
        result = subprocess.run([
            "ollama", "list"
        ], capture_output=True, text=True)
        if result.returncode != 0:
            return None, f"Ollama not found. Please install it from {OLLAMA_GITHUB_URL}"
        models = []
        for line in result.stdout.strip().split('\n'):
            if line and not line.startswith('NAME'):
                models.append(line.split()[0])
        # If no models found, prompt user to download the default model
        if not models:
            print(
                f"[CodeZ CLI] No Ollama models found on your system.\n"
                f"Would you like to download and run the default model ([bold]{DEFAULT_MODEL}[/bold]) now? [y/N]"
            )
            try:
                user_input = input("Download and run default model? [y/N]: ").strip().lower()
            except EOFError:
                user_input = "n"
            if user_input in ["y", "yes"]:
                print(f"[CodeZ CLI] Downloading and running default model: {DEFAULT_MODEL} ...")
                try:
                    pull_result = subprocess.run(
                        ["ollama", "run", DEFAULT_MODEL, "Hello!"],
                        capture_output=True,
                        text=True
                    )
                    if pull_result.returncode == 0:
                        print(f"[CodeZ CLI] Model '{DEFAULT_MODEL}' downloaded and ready.")
                        # Try listing again
                        return get_ollama_models()
                    else:
                        return None, f"Failed to download model '{DEFAULT_MODEL}'. Please try manually: ollama run {DEFAULT_MODEL}"
                except Exception as e:
                    return None, f"Error downloading model '{DEFAULT_MODEL}': {e}"
            else:
                return None, f"No models found. Please download a model using: ollama run {DEFAULT_MODEL}"
        return models, None
    except FileNotFoundError:
        return None, f"Ollama not found. Please install it from {OLLAMA_GITHUB_URL}"


def fetch_webpage(query, urls):
    return {"content": f"[Web search not available in this environment. Simulated result for: {query}]"}
