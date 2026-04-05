import os
import uuid
from dotenv import load_dotenv
from cryptography.fernet import Fernet

# teaching comment:
# Use a *relative* import inside this package. That way it works whether you run
# `python main.py` from `src/web/` (sibling package `email_system`) or you start
# the app as a module from the repo root (`python -m src.web.main`). Relative
# imports do not depend on the repo root being on `PYTHONPATH`.
from .email_smtp_config import send_email


def encrypt_email(email: str) -> str:
    """
    Encrypt an email string using Fernet symmetric encryption.
    """
    load_dotenv()
    fernet_email_enc_key = os.getenv("FERNET_EMAIL_ENC_KEY")
    if not fernet_email_enc_key:
        raise ValueError("FERNET_EMAIL_ENC_KEY is not set - Use the utility script found in basic website")
    encrypted_email = Fernet(fernet_email_enc_key).encrypt(email.encode())
    return encrypted_email.decode()


def generate_manage_token() -> str:
    """
    Generate a random UUIDv4 string to be used as a magic manage-token.
    """
    return str(uuid.uuid4())


def send_magic_link_email(email: str, token: str) -> None:
    """
    Send a magic-link email to user.
    """
    send_email(
        email,
        "Magic Link",
        f"Click the link to manage your account: {os.getenv('FRONTEND_URL')}/manage?token={token}",
    )

