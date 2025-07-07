# core/licensing.py

# core/licensing.py
import re
from core.user_config import save_license_key, load_license_key, clear_license_key

# For messaging from this module, we'd ideally pass a console object or use logging.
# For simplicity in this step, direct print will be used, assuming it's for CLI feedback.
# from rich.console import Console
# console = Console() # Avoid creating global console here if not necessary for all functions

# Simulated valid license key pattern (example: CODEZPRO-A1B2-C3D4-E5F6-G7H8)
VALID_KEY_PATTERN = re.compile(r"^CODEZPRO(-[A-Z0-9]{4}){4}$")
DUMMY_VALID_KEY = "CODEZPRO-TEST-DUMY-VALD-PROK" # A specific dummy key that "works"

def is_pro_license_active() -> bool:
    """
    Checks if a Pro license is currently stored and considered active.
    This is a simplified check based on the presence and format of a stored key.
    """
    stored_key = load_license_key()
    if stored_key:
        # In a real system, validation would be more complex (e.g., checking a signature, expiry)
        # For this step, we'll consider any key matching our DUMMY_VALID_KEY as "active".
        return stored_key == DUMMY_VALID_KEY # or VALID_KEY_PATTERN.match(stored_key)
    return False

def activate_pro_license(key: str) -> tuple[bool, str]:
    """
    Attempts to "activate" a Pro license with the given key.
    Stores the key if it matches a (dummy) valid format/value.
    """
    key = key.strip().upper()
    # Simulate validation (e.g., pattern match or check against a known dummy key)
    if key == DUMMY_VALID_KEY: # Or VALID_KEY_PATTERN.match(key):
        save_license_key(key)
        return True, f"Pro license activated successfully with key: {key}"
    elif VALID_KEY_PATTERN.match(key): # Matches format but not the DUMMY_VALID_KEY
        # This case simulates a key that looks right but isn't the special one we "accept" locally
        return False, f"License key '{key}' has a valid format, but is not recognized as an active Pro key in this demo. (Hint: try the dummy key mentioned in Pro feature messages)."
    else:
        return False, f"Invalid license key format: '{key}'. Expected format: CODEZPRO-XXXX-XXXX-XXXX-XXXX"

def deactivate_pro_license() -> tuple[bool, str]:
    """
    Deactivates and clears the stored Pro license.
    """
    if load_license_key():
        clear_license_key()
        return True, "Pro license deactivated and cleared from local config."
    else:
        return False, "No active Pro license found to deactivate."

def get_license_status_message() -> str:
    """
    Returns a message about the current license status.
    """
    if is_pro_license_active():
        key = load_license_key()
        return f"[bold green]Pro License: ACTIVE[/bold green]\nKey: {key}"
    else:
        stored_key = load_license_key()
        if stored_key: # A key is stored but not considered active by is_pro_license_active() logic
            return "[bold yellow]Pro License: INACTIVE[/bold yellow]\nStored key found but not currently validated as active Pro."
        return "[bold red]Pro License: INACTIVE[/bold red]\nNo active Pro license found."
