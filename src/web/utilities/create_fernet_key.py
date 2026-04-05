"""
Utility script to create or rotate the FERNET_EMAIL_ENC_KEY used for Fernet encryption.
"""

from __future__ import annotations

from pathlib import Path
from cryptography.fernet import Fernet


def find_env_file() -> Path:
    """
    Find the .env file at the project root.
    """
    base_dir = Path(__file__).resolve().parent
    return base_dir.parents[2] / ".env"


def load_env_lines(env_path: Path) -> list[str]:
    if not env_path.exists():
        return []
    return env_path.read_text(encoding="utf-8").splitlines()


def write_env_lines(env_path: Path, lines: list[str]) -> None:
    text = "\n".join(lines) + "\n"
    env_path.write_text(text, encoding="utf-8")


def main() -> None:
    env_path = find_env_file()
    print(f"Using .env at: {env_path}")
    lines = load_env_lines(env_path)

    existing_line = next((line for line in lines if line.strip().startswith("FERNET_EMAIL_ENC_KEY=")), None)

    if existing_line:
        print("\nAn FERNET_EMAIL_ENC_KEY already exists in your .env:")
        print(f"  {existing_line[:40]}...")
        print(
            "\nIf you overwrite this key, ALL previously encrypted emails "
            "will become unreadable. You will NOT be able to recover them."
        )
        confirm = input("Type EXACTLY 'OVERWRITE' to generate a new key, or anything else to cancel: ").strip()
        if confirm != "OVERWRITE":
            print("Aborted. Existing FERNET_EMAIL_ENC_KEY left unchanged.")
            return
    else:
        print("\nNo FERNET_EMAIL_ENC_KEY found in .env; a new one will be created.")

    new_key = Fernet.generate_key().decode("utf-8")
    filtered = [line for line in lines if not line.strip().startswith("FERNET_EMAIL_ENC_KEY=")]
    filtered.append(f"FERNET_EMAIL_ENC_KEY={new_key}")
    env_path.parent.mkdir(parents=True, exist_ok=True)
    write_env_lines(env_path, filtered)
    print(f"Updated {env_path} with a new FERNET_EMAIL_ENC_KEY.")


if __name__ == "__main__":
    main()

