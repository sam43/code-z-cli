import pytest
import os
from src import permission_manager

def test_request_user_permission_auto_confirm_true(monkeypatch):
    monkeypatch.setenv('AUTO_CONFIRM', 'true')
    assert permission_manager.request_user_permission("Test auto confirm?") is True

def test_request_user_permission_auto_confirm_false(monkeypatch):
    monkeypatch.setenv('AUTO_CONFIRM', 'false')
    # Need to simulate input if AUTO_CONFIRM is false
    monkeypatch.setattr('builtins.input', lambda _: 'yes')
    assert permission_manager.request_user_permission("Test with input (yes)?") is True

    monkeypatch.setattr('builtins.input', lambda _: 'no')
    assert permission_manager.request_user_permission("Test with input (no)?") is False

def test_request_user_permission_yes_input(monkeypatch):
    # Ensure AUTO_CONFIRM is not set or is false
    monkeypatch.delenv('AUTO_CONFIRM', raising=False)
    monkeypatch.setattr('builtins.input', lambda _: 'yes')
    assert permission_manager.request_user_permission("Grant permission (yes)?") is True

    monkeypatch.setattr('builtins.input', lambda _: 'y')
    assert permission_manager.request_user_permission("Grant permission (y)?") is True

def test_request_user_permission_no_input(monkeypatch):
    monkeypatch.delenv('AUTO_CONFIRM', raising=False)
    monkeypatch.setattr('builtins.input', lambda _: 'no')
    assert permission_manager.request_user_permission("Grant permission (no)?") is False

    monkeypatch.setattr('builtins.input', lambda _: 'n')
    assert permission_manager.request_user_permission("Grant permission (n)?") is False

def test_request_user_permission_invalid_then_valid_input(monkeypatch, capsys):
    monkeypatch.delenv('AUTO_CONFIRM', raising=False)
    inputs = iter(['maybe', 'yes']) # Simulate user typing "maybe", then "yes"
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))

    assert permission_manager.request_user_permission("Grant with invalid then valid?") is True
    captured = capsys.readouterr()
    assert "Invalid input. Please answer 'yes' or 'no'." in captured.out

def test_verify_consent_delegates_to_request(monkeypatch):
    # Test that verify_consent effectively uses the same logic as request_user_permission
    action_desc = "perform a test action"

    monkeypatch.setenv('AUTO_CONFIRM', 'true')
    assert permission_manager.verify_consent(action_desc) is True
    del os.environ['AUTO_CONFIRM'] # Clean up

    monkeypatch.setattr('builtins.input', lambda _: 'no')
    assert permission_manager.verify_consent(action_desc) is False

def test_request_user_permission_eof_error(monkeypatch):
    monkeypatch.delenv('AUTO_CONFIRM', raising=False)
    def raise_eof_error(_):
        raise EOFError
    monkeypatch.setattr('builtins.input', raise_eof_error)
    assert permission_manager.request_user_permission("Test EOFError?") is False

# KeyboardInterrupt is harder to simulate reliably in pytest without subprocesses
# or more complex signal handling tests, so we'll trust the handler code for now.

# Note: To run these tests, you'll need pytest installed.
# (e.g., pip install pytest pytest-asyncio)
# And run `pytest` in the terminal from the root directory.
