"""
Mode management and permission system for automatic code editing (build mode).
Follows clean architecture and SOLID principles.
"""
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import difflib
import tempfile
import shutil

class OperationMode(Enum):
    ASK = "ask"
    BUILD = "build"

class PermissionLevel(Enum):
    NONE = auto()
    ONCE = auto()
    ALL = auto()
    GLOBAL = auto()

class FileChange:
    def __init__(self, file_path: str, original_content: str, new_content: str, operation: str):
        self.file_path = file_path
        self.original_content = original_content
        self.new_content = new_content
        self.operation = operation  # 'edit', 'create', 'delete'
        self.applied = False
        self.backup_path: Optional[str] = None

    def get_diff(self) -> str:
        """Return unified diff preview."""
        orig = self.original_content.splitlines(keepends=True)
        new = self.new_content.splitlines(keepends=True)
        diff = difflib.unified_diff(
            orig, new,
            fromfile=f"a/{self.file_path}",
            tofile=f"b/{self.file_path}",
            lineterm=""
        )
        return ''.join(diff)

class ModeManager:
    def __init__(self):
        self.current_mode = OperationMode.ASK
        self.permissions: Dict[str, PermissionLevel] = {}
        self.pending_changes: List[FileChange] = []
        self.global_permission: Optional[PermissionLevel] = None
        self.temp_dir: Optional[str] = None

    def set_mode(self, mode: str) -> str:
        try:
            new_mode = OperationMode(mode.lower())
        except ValueError:
            return "❌ Invalid mode. Use: /mode ask or /mode build"
        if new_mode == self.current_mode:
            return f"Already in {new_mode.value.upper()} mode."
        self.current_mode = new_mode
        if new_mode == OperationMode.BUILD:
            self._init_build_mode()
            return "✅ Switched to BUILD mode. I can now edit files automatically with your permission."
        else:
            self._cleanup_build_mode()
            return "✅ Switched to ASK mode. I'll only suggest code, not edit files."

    def _init_build_mode(self):
        self.temp_dir = tempfile.mkdtemp(prefix="codez_build_")
        self.pending_changes.clear()
        self.permissions.clear()
        self.global_permission = None

    def _cleanup_build_mode(self):
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
        self.pending_changes.clear()
        self.permissions.clear()
        self.global_permission = None

    def is_build_mode(self) -> bool:
        return self.current_mode == OperationMode.BUILD

    def can_edit_file(self, file_path: str) -> Tuple[bool, str]:
        if not self.is_build_mode():
            return False, "Not in build mode."
        if self.global_permission == PermissionLevel.GLOBAL:
            return True, "Global permission granted."
        perm = self.permissions.get(file_path, PermissionLevel.NONE)
        if perm in (PermissionLevel.ALL, PermissionLevel.ONCE):
            return True, f"File permission: {perm.name}"
        return False, "Permission required."

    def add_pending_change(self, change: FileChange):
        self.pending_changes.append(change)

    def request_permission_message(self, file_path: str, operation: str, diff_preview: str) -> str:
        preview = diff_preview[:500] + ('...' if len(diff_preview) > 500 else '')
        return (
            f"\n🔧 **BUILD MODE: Permission Required**\n\n"
            f"**File**: `{file_path}`\n"
            f"**Operation**: {operation}\n\n"
            f"**Preview of changes**:\n"
            f"```diff\n{preview}\n```\n"
            "Choose your response:\n\n"
            "accept once - Apply this change only\n"
            "accept all - Apply this and all future changes to this file\n"
            "accept global - Apply all changes to all files (until mode switch)\n"
            "reject - Skip this change\n"
            "show full - Show complete diff\n"
        )

    def handle_permission_response(self, response: str, file_path: str) -> Tuple[bool, str]:
        resp = response.strip().lower()
        if resp == "accept once":
            self.permissions[file_path] = PermissionLevel.ONCE
            return True, "Accepted once."
        elif resp == "accept all":
            self.permissions[file_path] = PermissionLevel.ALL
            return True, "Accepted all for this file."
        elif resp == "accept global":
            self.global_permission = PermissionLevel.GLOBAL
            return True, "Accepted all for all files."
        elif resp == "reject":
            self.permissions[file_path] = PermissionLevel.NONE
            return False, "Change rejected."
        elif resp == "show full":
            return False, "Show full diff."
        else:
            return False, "Unrecognized response."

    def apply_change(self, change: FileChange) -> bool:
        """Apply the file change if permitted."""
        if not self.can_edit_file(change.file_path)[0]:
            return False
        # Backup original file
        file_path = Path(change.file_path)
        if file_path.exists():
            backup = Path(self.temp_dir) / (file_path.name + ".bak")
            shutil.copy2(file_path, backup)
            change.backup_path = str(backup)
        # Write new content
        file_path.write_text(change.new_content, encoding="utf-8")
        change.applied = True
        return True

    def revert_change(self, change: FileChange) -> bool:
        """Revert a previously applied change."""
        if not change.applied or not change.backup_path:
            return False
        file_path = Path(change.file_path)
        backup = Path(change.backup_path)
        if backup.exists():
            shutil.copy2(backup, file_path)
            change.applied = False
            return True
        return False

    def clear_permissions(self):
        self.permissions.clear()
        self.global_permission = None

    def list_pending_changes(self) -> List[FileChange]:
        return self.pending_changes

    def cleanup(self):
        self._cleanup_build_mode()
