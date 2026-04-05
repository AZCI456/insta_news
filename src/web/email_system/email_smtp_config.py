# resend_smtp_config.py

"""
Helper for sending emails via Resend SMTP.
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

SMTP_SERVER = "smtp.resend.com"
SMTP_PORT = 587
SMTP_USER = "resend"
SENDER = "onboarding@resend.dev"


def send_email(
    receiver: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
) -> None:
    """
    Send a single email via Resend's SMTP endpoint.
    """
    api_key = os.getenv("API_KEY_RESEND")
    if not api_key:
        raise RuntimeError("API_KEY_RESEND is not set in .env; cannot authenticate to Resend.")

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


if __name__ == "__main__":
    test_recipient = os.getenv("TESTING_EMAIL_RECIPIENT")
    if not test_recipient:
        raise RuntimeError("TESTING_EMAIL_RECIPIENT is not set in .env; set it to your test inbox.")

    send_email(
        receiver=test_recipient,
        subject="README.MOFO",
        text_body="Sigma the front lines await your arrival... STRAP UP!",
        html_body=("<p>Sigma the front lines await your arrival... " "<strong>STRAP UP</strong>!</p>"),
    )
    print("Test email sent successfully via Resend SMTP.")

