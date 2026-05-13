"""
Helper for sending emails via Amazon SES SMTP.
"""

from __future__ import annotations

import os
import ssl
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class SesSmtpSettings:
    """
    Runtime settings needed to authenticate to Amazon SES' SMTP endpoint.
    """

    host: str
    port: int
    username: str
    password: str
    sender: str
    region: str | None


def _first_env(*names: str) -> str | None:
    """
    Return the first non-empty env var from a list of supported names.
    """
    for name in names:
        value = os.getenv(name)
        if value:
            stripped = value.strip()
            if stripped:
                return stripped
    return None


def get_ses_smtp_settings() -> SesSmtpSettings:
    """
    Read SES SMTP settings from environment variables.

    `SMTP_USERNAME`/`SMTP_PASSWORD` are the SES SMTP credentials from the AWS
    SES console. They are different from IAM access keys, even though AWS
    creates them from an IAM user behind the scenes.
    """
    username = _first_env("SMTP_USERNAME", "AWS_SES_SMTP_USERNAME", "SES_SMTP_USERNAME")
    password = _first_env("SMTP_PASSWORD", "AWS_SES_SMTP_PASSWORD", "SES_SMTP_PASSWORD")
    sender = _first_env("SES_FROM_EMAIL", "SMTP_FROM_EMAIL", "TESTING_EMAIL_RECIPIENT")
    region = _first_env("SES_REGION", "AWS_REGION", "AWS_DEFAULT_REGION")
    host = _first_env("SES_SMTP_HOST")

    missing = []
    if not username:
        missing.append("SMTP_USERNAME")
    if not password:
        missing.append("SMTP_PASSWORD")
    if not sender:
        missing.append("SES_FROM_EMAIL")
    if not host and not region:
        missing.append("SES_REGION")
    if missing:
        raise RuntimeError(
            "Missing SES SMTP config: "
            + ", ".join(missing)
            + ". Set these in .env locally and in your deployment environment."
        )

    # teaching comment:
    # SES SMTP endpoints are regional. If you generated SMTP credentials in
    # Sydney, for example, the app must connect to `email-smtp.ap-southeast-2.amazonaws.com`.
    smtp_host = host or f"email-smtp.{region}.amazonaws.com"
    smtp_port = int(_first_env("SES_SMTP_PORT", "SMTP_PORT") or "587")

    return SesSmtpSettings(
        host=smtp_host,
        port=smtp_port,
        username=username,
        password=password,
        sender=sender,
        region=region,
    )


def send_email(
    receiver: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
) -> None:
    """
    Send a single email via Amazon SES SMTP.
    """
    settings = get_ses_smtp_settings()

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.sender
    msg["To"] = receiver
    msg.set_content(text_body)

    if html_body is not None:
        msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(settings.host, settings.port, timeout=30) as server:
        server.starttls(context=ssl.create_default_context())
        server.login(settings.username, settings.password)
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
    print("Test email sent successfully via Amazon SES SMTP.")

