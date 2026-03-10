# resend_smtp_config.py

"""
Helper for sending emails via Resend SMTP.

- You can import send_resend_email(...) from other modules.
- You can also run this file directly to send a test email.
"""

# Teaching comment:
# In older versions of Python (before 3.7), if you referred to a class/type in a function signature
# that hadn't been defined yet, you'd get an error. Example:
#   def foo(bar: MyType): ...
# This line lets you write type hints referencing classes that are defined later in the file,
# or even do recursive type hints (e.g. for a tree structure that refers to itself).
# In Python 3.7+, this is less often needed; in Python 3.10+, all annotations are 'lazy' by default in some contexts.
# Nowadays, it's mostly used for compatibility and consistency across versions.
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (two levels up from this file).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

SMTP_SERVER = "smtp.resend.com"
SMTP_PORT = 587
SMTP_USER = "resend"  # Resend expects this literal username for SMTP
SENDER = "onboarding@resend.dev"  # Change once you have your own sender


def send_email(
    receiver: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
) -> None:
    """
    Send a single email via Resend's SMTP endpoint.

    - receiver: email address of the recipient
    - subject: subject line
    - text_body: plain‑text body
    - html_body: optional HTML body (for rich clients)
    """
    api_key = os.getenv("API_KEY_RESEND")
    if not api_key:
        raise RuntimeError(
            "API_KEY_RESEND is not set in .env; cannot authenticate to Resend."
        )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SENDER
    msg["To"] = receiver
    msg.set_content(text_body)

    if html_body is not None:
        msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, api_key)
        server.send_message(msg)


# run this as a test but never import the file otherwise will cause naming conflicts
if __name__ == "__main__":
    # Simple manual test when you run: python resend_smtp_config.py
    test_recipient = os.getenv("TESTING_EMAIL_RECIPIENT")
    if not test_recipient:
        raise RuntimeError(
            "TESTING_EMAIL_RECIPIENT is not set in .env; set it to your test inbox."
        )

    send_email(
        receiver=test_recipient,
        subject="README.MOFO",
        text_body="Sigma the front lines await your arrival... STRAP UP!",
        html_body=(
            "<p>Sigma the front lines await your arrival... "
            "<strong>STRAP UP</strong>!</p>"
        ),
    )
    print("Test email sent successfully via Resend SMTP.")