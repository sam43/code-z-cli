"""
Simple CLI access point for ModeManager feature demonstration and testing.
"""
import sys
from core.mode_manager import ModeManager, FileChange

def main():
    mm = ModeManager()
    print("Welcome to CodeZ Build Mode Demo CLI!")
    while True:
        cmd = input("\nEnter command (/mode <ask|build>, /edit <file>, /pending, /exit): ").strip()
        if cmd.startswith("/mode"):
            _, mode = cmd.split(maxsplit=1)
            print(mm.set_mode(mode))
        elif cmd.startswith("/edit"):
            if not mm.is_build_mode():
                print("Not in build mode. Use /mode build first.")
                continue
            _, file_path = cmd.split(maxsplit=1)
            try:
                orig = open(file_path, encoding="utf-8").read()
            except Exception:
                orig = ""
            print("Enter new content (end with a single line containing only 'END'):")
            lines = []
            while True:
                l = input()
                if l.strip() == "END":
                    break
                lines.append(l)
            new_content = "\n".join(lines)
            change = FileChange(file_path, orig, new_content, "edit")
            mm.add_pending_change(change)
            diff = change.get_diff()
            print(mm.request_permission_message(file_path, "edit", diff))
            resp = input("Your response: ")
            allowed, msg = mm.handle_permission_response(resp, file_path)
            print(msg)
            if allowed:
                if mm.apply_change(change):
                    print(f"Change applied to {file_path}.")
                else:
                    print("Permission denied or error applying change.")
            else:
                print("Change not applied.")
        elif cmd == "/pending":
            for c in mm.list_pending_changes():
                print(f"{c.file_path}: applied={c.applied}")
        elif cmd == "/exit":
            print("Exiting.")
            break
        else:
            print("Unknown command.")

if __name__ == "__main__":
    main()
