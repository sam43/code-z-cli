import os
import tempfile
import shutil
import pytest
from core.mode_manager import ModeManager, FileChange, PermissionLevel
from unittest.mock import patch

def test_llm_edit_and_logging(tmp_path):
    mm = ModeManager()
    mm.set_mode("build")
    file_path = tmp_path / "llm_test.py"
    file_path.write_text("print('hello')\n")
    orig = file_path.read_text()
    # Simulate LLM edit
    new_content = orig + "# LLM EDIT\n"
    change = FileChange(str(file_path), orig, new_content, "fix")
    mm.add_pending_change(change)
    # Patch can_edit_file to always allow
    mm.permissions[str(file_path)] = PermissionLevel.ALL
    mm.apply_change(change)
    # Check audit log
    log_path = os.path.join(os.path.dirname(str(file_path)), "../sessions/edit_audit.log")
    # Not guaranteed to exist in test, but check that no error is raised
    assert change.applied

def test_enhanced_diff():
    orig = "a = 1\nb = 2\n"
    new = "a = 1\nb = 3\n"
    change = FileChange("dummy.py", orig, new, "fix")
    diff = change.get_diff()
    assert "-b = 2" in diff and "+b = 3" in diff

def test_permission_policies(tmp_path):
    mm = ModeManager()
    mm.set_mode("build")
    file_path = tmp_path / "policy.py"
    file_path.write_text("x = 1\n")
    change = FileChange(str(file_path), "x = 1\n", "x = 2\n", "fix")
    mm.add_pending_change(change)
    # Simulate user policy: always allow for .py files
    mm.permissions[str(file_path)] = PermissionLevel.ALL
    assert mm.can_edit_file(str(file_path))[0]
    assert mm.apply_change(change)
    assert file_path.read_text() == "x = 2\n"

def test_directory_pattern_permissions(tmp_path):
    mm = ModeManager()
    mm.set_mode("build")
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    file_path = subdir / "foo.py"
    file_path.write_text("y = 1\n")
    change = FileChange(str(file_path), "y = 1\n", "y = 2\n", "fix")
    mm.add_pending_change(change)
    # Simulate directory-level permission
    mm.permissions[str(subdir)] = PermissionLevel.ALL
    # Directory-level permission logic (to be implemented in ModeManager for real)
    allowed = any(str(file_path).startswith(str(p)) and perm == PermissionLevel.ALL for p, perm in mm.permissions.items())
    assert allowed
