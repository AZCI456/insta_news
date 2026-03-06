"""
Utility script to create or rotate the FERNET_EMAIL_ENC_KEY used for Fernet encryption.

Run this manually, e.g.:

    cd basic_website
    python setup_fernet_key.py

It will:
- Locate your project .env file (one level up from basic_website).
- Warn you if an FERNET_EMAIL_ENC_KEY already exists.
- Ask for confirmation before overwriting.
- Write a fresh random key into .env.
"""

from __future__ import annotations

from pathlib import Path

from cryptography.fernet import Fernet


def find_env_file() -> Path:
    """
    Find the .env file at the project root.

    We assume this script lives in basic_website/, so the project root
    (where your other tooling already keeps .env) is one directory up.
    """
    base_dir = Path(__file__).resolve().parent
    return base_dir.parent / ".env"


def load_env_lines(env_path: Path) -> list[str]:
    """
    Return existing .env lines if the file exists, otherwise [].
    """
    if not env_path.exists():
        return []
    return env_path.read_text(encoding="utf-8").splitlines()


def write_env_lines(env_path: Path, lines: list[str]) -> None:
    """
    Overwrite the .env file with the provided lines.

    This keeps other environment variables intact while updating FERNET_EMAIL_ENC_KEY.
    """
    text = "\n".join(lines) + "\n"
    env_path.write_text(text, encoding="utf-8")


def main() -> None:
    env_path = find_env_file()
    print(f"Using .env at: {env_path}")

    lines = load_env_lines(env_path)

    # Look for an existing FERNET_EMAIL_ENC_KEY line (if any).
    existing_line = next(
        (line for line in lines if line.strip().startswith("FERNET_EMAIL_ENC_KEY=")), None
    )

    if existing_line:
        print("\nAn FERNET_EMAIL_ENC_KEY already exists in your .env:")
        # Only show a small prefix to avoid accidentally leaking the full key on screen.
        print(f"  {existing_line[:40]}...")
        print(
            "\nIf you overwrite this key, ALL previously encrypted emails "
            "will become unreadable. You will NOT be able to recover them."
        )
        confirm = input(
            "Type EXACTLY 'OVERWRITE' to generate a new key, or anything else to cancel: "
        ).strip()
        if confirm != "OVERWRITE":
            print("Aborted. Existing FERNET_EMAIL_ENC_KEY left unchanged.")
            return
    else:
        print("\nNo FERNET_EMAIL_ENC_KEY found in .env; a new one will be created.")

    # Generate a fresh random Fernet key. This is a URL-safe base64-encoded 32-byte key.
    new_key = Fernet.generate_key().decode("utf-8")
    print("\nGenerated new FERNET_EMAIL_ENC_KEY (hidden).")

    # Filter out any old FERNET_EMAIL_ENC_KEY line(s), keep all other env vars as-is.
    filtered = [line for line in lines if not line.strip().startswith("FERNET_EMAIL_ENC_KEY=")]
    filtered.append(f"FERNET_EMAIL_ENC_KEY={new_key}")

    # If the file didn't exist before, make sure parent directory does.
    env_path.parent.mkdir(parents=True, exist_ok=True)
    write_env_lines(env_path, filtered)

    print(f"Updated {env_path} with a new FERNET_EMAIL_ENC_KEY.")
    print(
        "\nIMPORTANT:\n"
        "- Do NOT commit this .env file or the key to version control.\n"
        "- If you ever LOSE this key, you will NOT be able to decrypt existing emails.\n"
        "  (You would need to treat all encrypted email data as lost and re-collect it.)"
    )


if __name__ == "__main__":
    main()

