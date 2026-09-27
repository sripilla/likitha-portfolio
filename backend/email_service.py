"""
Sends contact-form notifications.

Two transports are supported:

1. Resend (HTTPS API) — preferred. Works on hosts that block outbound SMTP,
   such as Railway's Free/Hobby plans. Enabled when RESEND_API_KEY is set.
2. SMTP — fallback for local development or hosts that allow SMTP
   (e.g. Gmail with an App Password).

Both network calls are blocking, so they run in a thread via asyncio.to_thread
to avoid stalling the FastAPI event loop.
"""
import asyncio
import json
import logging
import smtplib
import urllib.error
import urllib.request
from email.message import EmailMessage

from .config import get_settings

logger = logging.getLogger("likitha_portfolio.email")
settings = get_settings()

RESEND_API_URL = "https://api.resend.com/emails"


def _build_subject_and_body(name: str, sender_email: str, message: str) -> tuple[str, str]:
    subject = f"Portfolio contact form: {name}"
    body = (
        f"New message from your portfolio site.\n\n"
        f"Name: {name}\n"
        f"Email: {sender_email}\n\n"
        f"Message:\n{message}"
    )
    return subject, body


def _send_via_resend(name: str, sender_email: str, message: str) -> None:
    subject, body = _build_subject_and_body(name, sender_email, message)
    payload = {
        "from": settings.RESEND_FROM_EMAIL,
        "to": [settings.CONTACT_RECEIVER_EMAIL],
        "reply_to": sender_email,
        "subject": subject,
        "text": body,
    }
    request = urllib.request.Request(
        RESEND_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status >= 300:
                raise RuntimeError(f"Resend returned HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Resend returned HTTP {exc.code}: {detail}") from exc


def _send_via_smtp(name: str, sender_email: str, message: str) -> None:
    subject, body = _build_subject_and_body(name, sender_email, message)
    email = EmailMessage()
    email["Subject"] = subject
    email["From"] = settings.SMTP_USERNAME
    email["To"] = settings.CONTACT_RECEIVER_EMAIL
    email["Reply-To"] = sender_email
    email.set_content(body)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        smtp.starttls()
        smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(email)


async def send_contact_notification(name: str, sender_email: str, message: str) -> bool:
    """Returns True if the email was sent, False otherwise (never raises)."""
    transport = settings.email_transport
    if transport is None:
        logger.warning("Email not configured (set RESEND_API_KEY or SMTP_* env vars) — skipping send.")
        return False

    sender = _send_via_resend if transport == "resend" else _send_via_smtp
    try:
        await asyncio.to_thread(sender, name, sender_email, message)
        return True
    except Exception:
        logger.exception("Failed to send contact form email via %s.", transport)
        return False
