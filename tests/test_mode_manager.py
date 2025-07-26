import os
import tempfile
import shutil
import pytest
from core.mode_manager import ModeManager, FileChange

def test_mode_switching():
    mm = ModeManager()
    assert mm.current_mode.name == "ASK"
    assert not mm.is_build_mode()
    assert "BUILD" in mm.set_mode("build")
    assert mm.is_build_mode()
    assert "ASK" in mm.set_mode("ask")
    assert not mm.is_build_mode()

def test_permission_flow(tmp_path):
    mm = ModeManager()
    mm.set_mode("build")
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello")
    change = FileChange(str(file_path), "hello", "world", "edit")
    mm.add_pending_change(change)
    diff = change.get_diff()
    # Accept once
    allowed, msg = mm.handle_permission_response("accept once", str(file_path))
    assert allowed
    assert mm.can_edit_file(str(file_path))[0]
    assert mm.apply_change(change)
    assert file_path.read_text() == "world"
    # Revert
    assert mm.revert_change(change)
    assert file_path.read_text() == "hello"

def test_global_permission(tmp_path):
    mm = ModeManager()
    mm.set_mode("build")
    file1 = tmp_path / "a.txt"
    file2 = tmp_path / "b.txt"
    file1.write_text("a")
    file2.write_text("b")
    c1 = FileChange(str(file1), "a", "A", "edit")
    c2 = FileChange(str(file2), "b", "B", "edit")
    mm.add_pending_change(c1)
    mm.add_pending_change(c2)
    allowed, _ = mm.handle_permission_response("accept global", str(file1))
    assert allowed
    assert mm.can_edit_file(str(file1))[0]
    assert mm.can_edit_file(str(file2))[0]
    assert mm.apply_change(c1)
    assert mm.apply_change(c2)
    assert file1.read_text() == "A"
    assert file2.read_text() == "B"

def test_reject_permission(tmp_path):
    mm = ModeManager()
    mm.set_mode("build")
    file_path = tmp_path / "test.txt"
    file_path.write_text("foo")
    change = FileChange(str(file_path), "foo", "bar", "edit")
    mm.add_pending_change(change)
    allowed, msg = mm.handle_permission_response("reject", str(file_path))
    assert not allowed
    assert not mm.can_edit_file(str(file_path))[0]
    assert not mm.apply_change(change)
