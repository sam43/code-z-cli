# version_utils.py
import tomllib  # or tomli if Python < 3.11

def get_version():
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]