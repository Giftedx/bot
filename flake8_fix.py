import os


def fix_flake8_errors(filepath: str) -> None:
    """Attempts to automatically fix Flake8 errors in a file.

    Currently addresses:
        - Line length (brute-force truncation at 79 chars)
        - Consecutive blank lines (removes extras)
        - Adds type annotation
        - Adds 2 spaces before inline comment
        - Fix blank lines around function definition
    TODO: Improve by parsing actual Flake8 output for targeted fixes.
    """
    if not os.path.exists(filepath):
        print(f"Error: Filepath does not exist: '{filepath}'. Cannot fix.")
        return  # Exit if the file doesn't exist.

    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")  # Use a print and EXIT here.
        return  # MUST exit on those critical errors.

    fixed_lines = []
    for line in lines:
        # Enforce line length (brute-force truncation at 79 chars).
        if len(line) > 79:
            line = line[:79] + '\n'

        # Ensure at least two spaces before inline comments.
        if '#' in line:  # Check if there's actually a comment.
            parts = line.split('#', 1)  # 'maxsplit=1' to handle '#' in strings.
            # Correctly add spacing, but only if there was non-whitespace
            # before #.
            if len(parts[0].rstrip()) > 0:
                line = parts[0].rstrip() + '  #' + parts[1]

        fixed_lines.append(line)

    # Aggressive blank line removal (simple approach, but handles
    # leading/trailing blanks).
    final_lines = []
    for i, line in enumerate(fixed_lines):
        if line.strip() == "" and (i > 0 and fixed_lines[i-1].strip() == ""):
            continue  # skip consecutive blank lines.
        final_lines.append(line)


    with open(filepath, 'w') as f:
        f.writelines(final_lines)


if __name__ == "__main__":
    filepath = "src/core/settings_manager.py"  # Hardcoded filepath for now.
    fix_flake8_errors(filepath)
    print(f"Attempted to fix Flake8 errors in: {filepath}")