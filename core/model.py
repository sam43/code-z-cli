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
        models_details = []
        lines = result.stdout.strip().split('\n')
        if len(lines) < 1: # No output or only header
            return [], None # Return empty list if no models found

        header = lines[0]
        # Dynamically find column indices based on header names to be robust
        # to potential changes in column order or new columns in `ollama list`
        try:
            name_col = header.index("NAME")
            id_col = header.index("ID")
            size_col = header.index("SIZE")
            modified_col = header.index("MODIFIED") # This finds start of "MODIFIED AGO"
        except ValueError:
            # Fallback or error if headers are not as expected
            # For now, let's assume fixed positions if dynamic fails or stick to name only
            # Or, more robustly, parse based on known header text widths if truly necessary
            # A simpler regex approach for parsing lines might be more stable than fixed indices.

            # Let's use a regex approach for robustness, matching columns based on typical content
            # Example line: llama3:latest                   a6990e6be28c    4.7 GB  3 weeks ago
            # Regex needs to account for variable whitespace
            line_regex = re.compile(r"^(?P<name>\S+)\s+(?P<id>\S+)\s+(?P<size>\S+\s\S+)\s+(?P<modified>.+)$")

            for line_str in lines[1:]: # Skip header
                match = line_regex.match(line_str)
                if match:
                    model_data = match.groupdict()
                    models_details.append({
                        "name": model_data["name"],
                        "id": model_data["id"],
                        "size": model_data["size"],
                        "modified": model_data["modified"].strip() # Ensure no trailing whitespace
                    })
                elif line_str.strip(): # If line is not empty and didn't match, maybe a simpler model listing
                    parts = line_str.split()
                    if len(parts) >= 1: # At least a name
                         models_details.append({
                            "name": parts[0],
                            "id": parts[1] if len(parts) > 1 else "N/A",
                            "size": parts[2] if len(parts) > 2 else "N/A", # Assuming size might be one word if not GB/MB
                            "modified": " ".join(parts[3:]) if len(parts) > 3 else "N/A"
                        })
            return models_details, None

        # The dynamic column index finding is complex due to "MODIFIED AGO" potentially.
        # The regex approach above is generally more resilient to spacing variations.
        # Sticking with the regex approach.

    except FileNotFoundError:
        return None, f"Ollama not found. Please install it from {OLLAMA_GITHUB_URL}"

def fetch_webpage(query, urls):
    return {"content": f"[Web search not available in this environment. Simulated result for: {query}]"}
