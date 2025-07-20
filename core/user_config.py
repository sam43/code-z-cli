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
    """
    Remove the saved model choice from the configuration file if it exists.
    
    If the configuration file or the "model" key does not exist, the function does nothing.
    """
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
    """
    Save a key-value pair to the application's JSON configuration file.
    
    If the configuration file or its directory does not exist, they are created. Existing configuration data is preserved unless overwritten by the provided key.
    """
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
    """
    Retrieve the value associated with a given key from the application's JSON configuration file.
    
    Parameters:
        key (str): The configuration key to retrieve.
    
    Returns:
        The value associated with the specified key, or None if the key is not found, the file does not exist, or the file cannot be read.
    """
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            try:
                config = json.load(f)
                return config.get(key)
            except Exception:
                return None
    return None

def save_system_prompt(prompt):
    """
    Save the provided prompt string as the "system_prompt" value in the user configuration file.
    
    Parameters:
        prompt (str): The system prompt text to store.
    """
    _save_config_value("system_prompt", prompt)

def load_system_prompt():
    """
    Load and return the saved system prompt from the user configuration file.
    
    Returns:
        str or None: The system prompt string if present, otherwise None.
    """
    return _load_config_value("system_prompt")