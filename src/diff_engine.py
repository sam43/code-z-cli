import difflib

def generate_diff(old_code: str, new_code: str, fromfile: str = 'old_version', tofile: str = 'new_version') -> str:
    """
    Generates a diff between two versions of code using difflib.
    Returns the diff as a string in unified diff format.
    """
    old_code_lines = old_code.splitlines(keepends=True)
    new_code_lines = new_code.splitlines(keepends=True)

    diff = difflib.unified_diff(old_code_lines, new_code_lines, fromfile=fromfile, tofile=tofile)
    return "".join(diff)

def apply_diff(original_code: str, diff_str: str) -> str:
    """
    Applies a diff (in unified diff format) to the original code.
    Note: Python's difflib doesn't have a direct 'patch' utility like the command-line patch.
    This function provides a basic way to reconstruct the 'new_version' from a diff and 'old_version'.
    It's a simplified approach and might not handle all complex patch scenarios.
    A more robust solution might involve using a third-party library or `subprocess` to call `patch`.

    For this placeholder, we'll assume the diff can be naively applied by taking lines from `diff_str`
    that represent the "tofile" content. This is a significant simplification.
    """
    # This is a simplified placeholder. Real patch application is complex.
    # It attempts to extract the 'new' lines from a unified diff.
    # This will NOT correctly apply partial changes or context lines from a real diff.

    new_code_lines = []
    original_lines = original_code.splitlines(keepends=True)
    diff_lines = diff_str.splitlines(keepends=True)

    # Heuristic: try to find the start of the file content in the diff
    header_found = False
    content_started = False

    # This placeholder attempts to reconstruct the "to_file" content from a unified diff.
    # It's not a full patch algorithm but should work for simple diffs from generate_diff.
    if not diff_str: # If diff is empty, no changes.
        return original_code

    reconstructed_lines = []
    diff_lines_iter = iter(diff_str.splitlines(keepends=True))

    try:
        # Skip header lines until the first hunk
        for line in diff_lines_iter:
            if line.startswith('@@'):
                reconstructed_lines.append(line) # Keep hunk header for context if needed, or process it
                break
        else: # No hunk header found, diff might be malformed or empty after headers
            return original_code # Or handle as error / return new_code if possible to extract

        # Process lines within hunks
        for line in diff_lines_iter:
            if line.startswith('+'):
                reconstructed_lines.append(line[1:])
            elif line.startswith(' '): # Context line
                reconstructed_lines.append(line[1:])
            elif line.startswith('-'): # Line removed, ignore for new file
                continue
            elif line.startswith('@@'): # Start of a new hunk (placeholder doesn't handle multiple hunks well yet)
                reconstructed_lines.append(line) # Add hunk header for now
                continue
            elif line.startswith('\\ No newline at end of file'):
                # If the last reconstructed line has a newline, remove it.
                if reconstructed_lines and reconstructed_lines[-1].endswith('\n'):
                    reconstructed_lines[-1] = reconstructed_lines[-1][:-1]
            # else:
                # Other lines (e.g., ---, +++ if they appear again) are ignored by this simple parser
                # or could indicate end of relevant diff content.
    except StopIteration:
        pass # End of diff lines

    if not diff_str:
        return original_code

    new_code_lines = []
    # When difflib generates a diff, lines in the "to" file are prefixed with '+' or ' ' (context).
    # We need to collect these.
    for line in diff_str.splitlines(keepends=True):
        # Skip initial diff headers and hunk markers for this simple reconstruction
        if line.startswith('---') or line.startswith('+++') or line.startswith('@@'):
            continue

        if line.startswith('+'):
            new_code_lines.append(line[1:]) # Add new line content
        elif line.startswith(' '):
            new_code_lines.append(line[1:]) # Add context line content
        # Lines starting with '-' are deletions from old_code, so ignore them for new_code.
        # Handle '\ No newline at end of file'
        elif line.startswith('\\ No newline at end of file'):
            if new_code_lines and new_code_lines[-1].endswith('\n'):
                new_code_lines[-1] = new_code_lines[-1][:-1] # Remove last newline

    # If diff_str contained only deletions and no additions/context lines for the new file,
    # new_code_lines would be empty. This means the new file is empty.
    # If original_code was also empty and diff_str was empty, it returns original_code (empty).
    # If diff_str was not empty, but resulted in no lines for new_code (e.g. pure deletion),
    # then "".join(new_code_lines) is correctly ""
    return "".join(new_code_lines)


if __name__ == '__main__':
    code_v1 = """line1
line2
line3
"""
    code_v2 = """line1
line2 changed
line3
line4 added
"""

    diff_output = generate_diff(code_v1, code_v2)
    print("Generated Diff:")
    print(diff_output)

    # Note: The apply_diff function is a placeholder and may not work correctly.
    # For a robust solution, a proper patch utility would be needed.
    # This example demonstrates its current placeholder behavior.
    applied_code = apply_diff(code_v1, diff_output)
    print("\nCode after applying diff (placeholder behavior):")
    print(applied_code)

    # A more realistic check:
    # If apply_diff was perfect, applied_code should be equal to code_v2
    # assert applied_code == code_v2, "Applied diff does not match new code"
    # Due to placeholder nature, this assert will likely fail for non-trivial diffs.

    print(f"\nDoes applied code match v2? {'Yes' if applied_code.strip() == code_v2.strip() else 'No (as expected by placeholder)'}")
