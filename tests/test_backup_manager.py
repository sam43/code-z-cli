import pytest
import os
import shutil
from src import backup_manager # Import the module itself

# Helper function to create dummy files
def create_dummy_files(base_path, file_specs):
    created_files = []
    for name, content in file_specs.items():
        file_path = base_path / name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            f.write(content)
        created_files.append(str(file_path))
    return created_files

@pytest.fixture
def temp_backup_dir(tmp_path, monkeypatch):
    """Fixture to set and manage a temporary backup directory."""
    backup_dir = tmp_path / ".test_backups"
    backup_dir.mkdir()
    monkeypatch.setattr(backup_manager, 'BACKUP_BASE_DIR', str(backup_dir))
    return str(backup_dir)

@pytest.fixture
def source_files(tmp_path):
    """Fixture to create some source files for backup."""
    source_dir = tmp_path / "source_data"
    source_dir.mkdir()
    files = {
        "file1.txt": "Content of file1.",
        "file2.log": "Log data in file2."
    }
    return create_dummy_files(source_dir, files)

def test_create_backup(temp_backup_dir, source_files):
    backup_id = backup_manager.create_backup(source_files, "test_backup_01")
    assert backup_id == "test_backup_01"

    backup_path = os.path.join(temp_backup_dir, backup_id)
    assert os.path.isdir(backup_path)
    assert os.path.exists(os.path.join(backup_path, "file1.txt"))
    assert os.path.exists(os.path.join(backup_path, "file2.log"))

    with open(os.path.join(backup_path, "file1.txt"), "r") as f:
        assert f.read() == "Content of file1."

def test_create_backup_generates_id(temp_backup_dir, source_files):
    backup_id = backup_manager.create_backup(source_files) # No ID provided
    assert backup_id is not None
    assert "backup_" in backup_id # Check if default naming convention is present

    backup_path = os.path.join(temp_backup_dir, backup_id)
    assert os.path.isdir(backup_path)
    assert os.path.exists(os.path.join(backup_path, "file1.txt"))

def test_create_backup_file_not_found(temp_backup_dir):
    with pytest.raises(FileNotFoundError):
        backup_manager.create_backup(["non_existent_file.txt"], "backup_fail")
    # Ensure backup directory was not created or was cleaned up
    assert not os.path.exists(os.path.join(temp_backup_dir, "backup_fail"))


def test_list_backups(temp_backup_dir, source_files):
    assert backup_manager.list_backups() == [] # Should be empty initially

    backup_manager.create_backup(source_files, "backup_A")
    backup_manager.create_backup(source_files, "backup_B")

    backups = backup_manager.list_backups()
    assert len(backups) == 2
    assert "backup_A" in backups
    assert "backup_B" in backups

def test_delete_backup(temp_backup_dir, source_files):
    backup_id = backup_manager.create_backup(source_files, "backup_to_delete")
    assert os.path.isdir(os.path.join(temp_backup_dir, backup_id))

    backup_manager.delete_backup(backup_id)
    assert not os.path.exists(os.path.join(temp_backup_dir, backup_id))
    assert backup_id not in backup_manager.list_backups()

def test_delete_non_existent_backup(temp_backup_dir):
    with pytest.raises(FileNotFoundError):
        backup_manager.delete_backup("non_existent_backup_id")

def test_restore_backup(temp_backup_dir, source_files, tmp_path):
    original_content_file1 = "Content of file1."
    backup_id = backup_manager.create_backup(source_files, "restore_test_backup")

    # Modify the source files before restoring
    modified_content = "Modified content."
    with open(source_files[0], "w") as f:
        f.write(modified_content)

    with open(source_files[0], "r") as f: # Verify modification
        assert f.read() == modified_content

    # Restore to original locations
    backup_manager.restore_backup(backup_id, source_files)

    with open(source_files[0], "r") as f:
        assert f.read() == original_content_file1 # Should be restored content

    # Test restoring to a new directory
    restore_target_dir = tmp_path / "restore_destination"
    restore_target_dir.mkdir()

    # Create target paths for restoration in the new directory
    target_restore_paths = [str(restore_target_dir / os.path.basename(f)) for f in source_files]

    backup_manager.restore_backup(backup_id, target_restore_paths)

    restored_file1_path = restore_target_dir / "file1.txt"
    assert restored_file1_path.exists()
    with open(restored_file1_path, "r") as f:
        assert f.read() == original_content_file1

def test_restore_backup_id_not_found(temp_backup_dir):
    with pytest.raises(FileNotFoundError):
        backup_manager.restore_backup("non_existent_id", ["some_target.txt"])

def test_restore_backup_no_target_paths(temp_backup_dir, source_files):
    backup_id = backup_manager.create_backup(source_files, "no_target_test")
    with pytest.raises(ValueError, match="Target paths must be provided"):
        backup_manager.restore_backup(backup_id, [])

def test_create_backup_existing_id_raises_error(temp_backup_dir, source_files):
    backup_manager.create_backup(source_files, "duplicate_id_test")
    with pytest.raises(FileExistsError):
        backup_manager.create_backup(source_files, "duplicate_id_test")
