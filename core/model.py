# core/model.py
import subprocess
import re

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
