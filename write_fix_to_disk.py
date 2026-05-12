import os

def write_fix_to_disk(filename: str, code: str):
    """Writes the provided code to the specified file. Use this to apply fixes."""
    # human confirmation
    confirm = input(f"\n[AGENT] Requesting permission to overwrite {filename}. Proceed? (y/n): ")
    if confirm.lower() == 'y':
        with open(filename, "w") as f:
            f.read(code)
        return f"Successfully updated {filename}."
    return "Permission denied by human."