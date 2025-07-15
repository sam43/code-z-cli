import os
import json
from platformdirs import user_config_dir

CONFIG_PATH = os.path.join(user_config_dir("codez"), "config.json")

def save_model_choice(model_name):
    config = {}
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            try:
                config = json.load(f)
            except Exception:
                config = {}
    config["model"] = model_name
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)

def load_model_choice():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            try:
                config = json.load(f)
                return config.get("model")
            except Exception:
                return None
    return None

def clear_model_choice():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            try:
                config = json.load(f)
            except Exception:
                config = {}
        if "model" in config:
            del config["model"]
            with open(CONFIG_PATH, "w") as f:
                json.dump(config, f)

def _save_config_value(key, value):
    config = {}
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            try:
                config = json.load(f)
            except Exception:
                config = {}
    config[key] = value
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)

def _load_config_value(key):
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            try:
                config = json.load(f)
                return config.get(key)
            except Exception:
                return None
    return None

def save_system_prompt(prompt):
    _save_config_value("system_prompt", prompt)

def load_system_prompt():
    return _load_config_value("system_prompt")