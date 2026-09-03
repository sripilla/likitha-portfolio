"""
Sends contact-form notifications via SMTP.

smtplib is blocking, so it's run in a thread via asyncio.to_thread to avoid
stalling the FastAPI event loop while waiting on the network.
"""
import asyncio
import logging
import smtplib
from email.message import EmailMessage

from .config import get_settings

logger = logging.getLogger("likitha_portfolio.email")
settings = get_settings()


def _send_sync(name: str, sender_email: str, message: str) -> None:
    email = EmailMessage()
    email["Subject"] = f"Portfolio contact form: {name}"
    email["From"] = settings.SMTP_USERNAME
    email["To"] = settings.CONTACT_RECEIVER_EMAIL
    email["Reply-To"] = sender_email
    email.set_content(
        f"New message from your portfolio site.\n\n"
        f"Name: {name}\n"
        f"Email: {sender_email}\n\n"
        f"Message:\n{message}"
    )

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        smtp.starttls()
        smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(email)


async def send_contact_notification(name: str, sender_email: str, message: str) -> bool:
    """Returns True if the email was sent, False otherwise (never raises)."""
    if not settings.email_enabled:
        logger.warning("Email not configured (missing SMTP env vars) — skipping send.")
        return False

    try:
        await asyncio.to_thread(_send_sync, name, sender_email, message)
        return True
    except Exception:
        logger.exception("Failed to send contact form email.")
        return False
