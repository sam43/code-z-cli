# core/model.py
import subprocess
import re

OLLAMA_GITHUB_URL = "https://github.com/ollama/ollama"

def query_ollama(prompt: str, model: str = "deepseek-r1:latest"):
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
        return models, None
    except FileNotFoundError:
        return None, f"Ollama not found. Please install it from {OLLAMA_GITHUB_URL}"

def fetch_webpage(query, urls):
    return {"content": f"[Web search not available in this environment. Simulated result for: {query}]"}
