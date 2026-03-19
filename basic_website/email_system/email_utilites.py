import hashlib
import random
import string
from dotenv import load_dotenv
import os
# Yes, you typically need to install both of these dependencies if you haven't already:
# - uuid: This is part of the Python standard library (no need to install).
# - cryptography.fernet: "cryptography" is NOT part of the standard library and DOES need to be installed.
#   You can install it with: pip install cryptography

import uuid  # This module is part of the Python standard library, so you do NOT need to install it.
from cryptography.fernet import Fernet  # You DO need to install the 'cryptography' package.

# In Python, importing between files in the same directory is a bit tricky.
# - If you run this script directly, `from email_smtp_config import send_email` works (bare import from same dir).
# - But if it's run as a module (e.g. as part of a larger app), you should use a *relative import*.

# Import must be relative to main.py file
from email_system.email_smtp_config import send_email


def encrypt_email(email: str) -> str:
    """
    Encrypt an email string using Fernet symmetric encryption (AES-256-CBC)

    Parameters:
    - email (str): The plaintext email address to encrypt.

    Returns:
    - str: The encrypted email, encoded in base64 text format.
    """
    load_dotenv()
    FERNET_EMAIL_ENC_KEY = os.getenv("FERNET_EMAIL_ENC_KEY")
    if not FERNET_EMAIL_ENC_KEY:
        raise ValueError("FERNET_EMAIL_ENC_KEY is not set - Use the utility script found in basic website")
    encrypted_email = Fernet(FERNET_EMAIL_ENC_KEY).encrypt(email.encode()) # Fernet encrypts bytes, hence .encode() -> UTF-8 encoded bytes
    print(f"Encrypted email: {encrypted_email.decode()}")
    return encrypted_email.decode() # store as str

def generate_manage_token() -> str:
    """
    Generate a random UUIDv4 string to be used as a magic manage-token.

    Returns:
    - str: A new UUIDv4 as a string.
    """
    return str(uuid.uuid4())

def send_magic_link_email(email: str, token: str) -> None:
    """
    Placeholder for sending a "magic link" email to user.

    Parameters:
    - email (str): The recipient's email address.
    - token (str): The unique token to embed in the link.

    Returns:
    - None
    """
    send_email(email, "Magic Link", f"Click the link to manage your account: {os.getenv('FRONTEND_URL')}/manage?token={token}")