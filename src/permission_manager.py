import os

def request_user_permission(message: str) -> bool:
    """
    Requests user permission via a command-line prompt.
    Returns True if permission is granted (user types 'yes' or 'y'), False otherwise.
    Checks for an environment variable 'AUTO_CONFIRM' which, if set to 'true',
    will automatically grant permission.
    """
    if os.environ.get('AUTO_CONFIRM', 'false').lower() == 'true':
        print(f"AUTO_CONFIRM enabled: Permission granted for '{message}'")
        return True

    while True:
        try:
            response = input(f"{message} (yes/no): ").strip().lower()
            if response in ['yes', 'y']:
                return True
            elif response in ['no', 'n']:
                return False
            else:
                print("Invalid input. Please answer 'yes' or 'no'.")
        except EOFError: # Handle cases where input stream is closed (e.g., in some test environments)
            print("EOFError encountered. Assuming 'no' for permission.")
            return False
        except KeyboardInterrupt:
            print("\nPermission request interrupted by user. Assuming 'no'.")
            return False


def verify_consent(action_description: str) -> bool:
    """
    Verifies user consent for a specific action.
    This is currently an alias for request_user_permission but could be expanded
    to include more complex logic, like checking pre-approved consents.
    """
    print(f"Verifying consent for action: {action_description}")
    return request_user_permission(f"Do you approve the following action: '{action_description}'?")


if __name__ == '__main__':
    print("Testing permission_manager.py...")

    # Test AUTO_CONFIRM
    os.environ['AUTO_CONFIRM'] = 'true'
    print("\nTesting with AUTO_CONFIRM=true:")
    if verify_consent("automatic test action 1"):
        print("AUTO_CONFIRM test 1 passed (permission granted).")
    else:
        print("AUTO_CONFIRM test 1 failed.")
    del os.environ['AUTO_CONFIRM']

    # Manual test
    print("\nTesting with manual input (AUTO_CONFIRM is off):")
    print("Please respond to the following prompts:")

    if request_user_permission("Grant permission for manual test A?"):
        print("Manual test A: Permission granted by user.")
    else:
        print("Manual test A: Permission denied by user.")

    if verify_consent("perform manual test action B"):
        print("Manual test B: Consent verified by user.")
    else:
        print("Manual test B: Consent not verified by user.")

    print("\nTesting finished.")
