"""
SES SMTP connection smoke test.

This script sends a simple "Hello World" email through Amazon SES SMTP.
It is intended as a quick connectivity/authentication check and is not
part of automated unit/integration test runs unless called directly.
"""

import argparse
import os
import smtplib
import ssl
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.web.email_system.email_smtp_config import get_ses_smtp_settings, send_email  # noqa: E402


def _masked(value: str) -> str:
    """
    Show enough of a secret-like value to identify which env var loaded.
    """
    return "*" * max(len(value) - 4, 0) + value[-4:]


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a smoke-test email through Amazon SES SMTP.")
    parser.add_argument(
        "--login-only",
        action="store_true",
        help="Authenticate to SES SMTP without sending an email.",
    )
    args = parser.parse_args()

    # Load the repo-root `.env` even when this file is run from `tests/`.
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv()

    settings = get_ses_smtp_settings()
    recipient_email = os.getenv("SES_TO_EMAIL") or os.getenv("TESTING_EMAIL_RECIPIENT")
    if not recipient_email:
        raise RuntimeError("Missing SES_TO_EMAIL or TESTING_EMAIL_RECIPIENT.")

    print("SES SMTP debug info:")
    print(f"  region={settings.region or '<custom host>'}")
    print(f"  host={settings.host}")
    print(f"  port={settings.port}")
    print(f"  from={settings.sender}")
    print(f"  to={recipient_email}")
    print(f"  smtp_username={_masked(settings.username)} (len={len(settings.username)})")
    print(f"  smtp_password={_masked(settings.password)} (len={len(settings.password)})")

    try:
        if args.login_only:
            # teaching comment:
            # This proves the endpoint, TLS handshake, username, and password are
            # accepted before we try sending to a verified SES identity.
            with smtplib.SMTP(settings.host, settings.port, timeout=30) as server:
                server.starttls(context=ssl.create_default_context())
                server.login(settings.username, settings.password)
            print("SES SMTP login succeeded.")
            return

        send_email(
            receiver=recipient_email,
            subject="SES test email",
            text_body="Hello World",
        )
    except smtplib.SMTPAuthenticationError as exc:
        raise SystemExit(
            "SES rejected the SMTP login. Check that SES_REGION matches the "
            "region where these SMTP credentials were created, and confirm "
            "you are using SES SMTP credentials rather than IAM access keys.\n"
            f"Raw SMTP error: {exc}"
        ) from exc

    print("Test email sent successfully via Amazon SES SMTP.")


if __name__ == "__main__":
    main()
