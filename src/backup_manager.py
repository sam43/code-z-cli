import os
import shutil
import uuid
from datetime import datetime

BACKUP_BASE_DIR = ".backups"

def create_backup(file_paths: list[str], backup_id: str = None) -> str:
    """
    Creates a backup of specified files.
    Each backup is stored in a subdirectory named with a unique ID (or provided ID)
    within BACKUP_BASE_DIR.
    Returns the backup ID.
    """
    if not os.path.exists(BACKUP_BASE_DIR):
        os.makedirs(BACKUP_BASE_DIR)

    if backup_id is None:
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"

    current_backup_path = os.path.join(BACKUP_BASE_DIR, backup_id)

    if os.path.exists(current_backup_path):
        # If a backup ID is explicitly provided and already exists, append a unique suffix
        # or raise an error, depending on desired behavior. Here, we'll raise an error.
        # If backup_id was None, this case is less likely due to uuid.
        raise FileExistsError(f"Backup directory {current_backup_path} already exists.")

    os.makedirs(current_backup_path)

    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                shutil.copy2(file_path, os.path.join(current_backup_path, os.path.basename(file_path)))
            except Exception as e:
                # Clean up partially created backup on error
                shutil.rmtree(current_backup_path)
                raise IOError(f"Error copying file {file_path} to backup: {e}")
        else:
            # Clean up partially created backup if a file is not found
            shutil.rmtree(current_backup_path)
            raise FileNotFoundError(f"File not found: {file_path}")

    print(f"Backup created successfully with ID: {backup_id} in {current_backup_path}")
    return backup_id

def restore_backup(backup_id: str, target_paths: list[str]) -> None:
    """
    Restores files from a specified backup ID to their original or specified target paths.
    The number of files in target_paths should match the number of files backed up under that ID
    if you want a direct restoration. The function will try to match based on basenames.
    If target_paths are directories, it will restore into those directories.
    """
    backup_path = os.path.join(BACKUP_BASE_DIR, backup_id)
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup with ID '{backup_id}' not found at {backup_path}")

    backed_up_files = [f for f in os.listdir(backup_path) if os.path.isfile(os.path.join(backup_path, f))]

    if not target_paths:
        raise ValueError("Target paths must be provided for restoration.")

    # This logic assumes target_paths correspond to the desired final locations of the backed-up files.
    # It will attempt to match backed up files to target paths by basename if target_paths are directories,
    # or use target_paths directly if they are full file paths.

    restored_something = False
    for i, target_path_or_dir in enumerate(target_paths):
        # Try to find a corresponding backed up file. This is a simple heuristic.
        # A more robust system might store metadata about original paths.

        # Scenario 1: target_path_or_dir is a full file path
        potential_filename = os.path.basename(target_path_or_dir)

        if potential_filename in backed_up_files:
            source_file = os.path.join(backup_path, potential_filename)
            dest_file = target_path_or_dir
        elif i < len(backed_up_files) and not os.path.isdir(target_path_or_dir):
            # Fallback: assume ordered correspondence if names don't match but it's not a dir
            source_file = os.path.join(backup_path, backed_up_files[i])
            dest_file = target_path_or_dir
        elif os.path.isdir(target_path_or_dir) and i < len(backed_up_files):
            # Scenario 2: target_path_or_dir is a directory
            source_file = os.path.join(backup_path, backed_up_files[i]) # take the i-th file from backup
            dest_file = os.path.join(target_path_or_dir, backed_up_files[i])
        else:
            print(f"Warning: Could not determine source for target '{target_path_or_dir}' or not enough files in backup.")
            continue

        # Ensure destination directory exists
        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
        try:
            shutil.copy2(source_file, dest_file)
            print(f"Restored '{source_file}' to '{dest_file}'")
            restored_something = True
        except Exception as e:
            print(f"Error restoring file {source_file} to {dest_file}: {e}")
            # Decide if we should continue or raise error

    if not restored_something:
        print(f"Warning: No files were restored for backup ID {backup_id}. Check target paths and backup contents.")


def list_backups() -> list[str]:
    """
    Lists available backup IDs (directory names within BACKUP_BASE_DIR).
    """
    if not os.path.exists(BACKUP_BASE_DIR):
        return []

    entries = os.listdir(BACKUP_BASE_DIR)
    backup_ids = [entry for entry in entries if os.path.isdir(os.path.join(BACKUP_BASE_DIR, entry))]
    return backup_ids

def delete_backup(backup_id: str) -> None:
    """
    Deletes a specific backup by its ID.
    """
    backup_path = os.path.join(BACKUP_BASE_DIR, backup_id)
    if os.path.exists(backup_path) and os.path.isdir(backup_path):
        shutil.rmtree(backup_path)
        print(f"Backup '{backup_id}' deleted successfully.")
    else:
        raise FileNotFoundError(f"Backup with ID '{backup_id}' not found at {backup_path}")


if __name__ == '__main__':
    # Example Usage
    DEMO_FILES_DIR = "demo_files_for_backup"
    os.makedirs(DEMO_FILES_DIR, exist_ok=True)

    file1_path = os.path.join(DEMO_FILES_DIR, "sample1.txt")
    file2_path = os.path.join(DEMO_FILES_DIR, "sample2.log")

    with open(file1_path, "w") as f:
        f.write("This is sample file 1.")
    with open(file2_path, "w") as f:
        f.write("This is sample file 2, a log file.")

    files_to_backup = [file1_path, file2_path]

    try:
        print(f"Available backups before: {list_backups()}")

        # Create a backup
        b_id = create_backup(files_to_backup)
        print(f"Created backup with ID: {b_id}")

        print(f"Available backups after creation: {list_backups()}")

        # Modify original files
        with open(file1_path, "w") as f:
            f.write("This is MODIFIED sample file 1.")

        # Restore files
        # For simplicity, restoring to original locations.
        # We need to provide the original paths as target_paths for this to work as expected.
        restore_backup(b_id, files_to_backup)

        with open(file1_path, "r") as f:
            content = f.read()
            print(f"Content of {file1_path} after restore: {content}")
            assert "This is sample file 1." in content

        # Delete the backup
        delete_backup(b_id)
        print(f"Available backups after deletion: {list_backups()}")

    except Exception as e:
        print(f"An error occurred during demo: {e}")
    finally:
        # Clean up demo files and backup directory
        if os.path.exists(DEMO_FILES_DIR):
            shutil.rmtree(DEMO_FILES_DIR)
        # Careful with this if you have other backups you want to keep
        # For demo purposes, we clean it.
        # if os.path.exists(BACKUP_BASE_DIR):
        #     shutil.rmtree(BACKUP_BASE_DIR)
        print("Demo finished.")
