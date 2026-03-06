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



EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def encrypt_email(email):
    load_dotenv()
    FERNET_KEY = os.getenv("FERNET_KEY")
    encrypted_email = Fernet(EMAIL_PASSWORD).encrypt(email.encode())
    return encrypted_email.decode()

# create a UUIDv4 identifer for the user to manage their account
def generate_manage_token():
    return str(uuid.uuid4())


def send_magic_link_email(email, token):
    pass