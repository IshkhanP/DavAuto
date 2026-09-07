"""Email delivery — pluggable backend (currently SMTP, easily swapped)."""
from __future__ import annotations
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Sends transactional emails.  Failures are logged but never raised — the
    application keeps working even when email delivery fails (so registration
    isn't blocked in environments without an SMTP server).
    """

    async def send(self, to: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
        if not settings.SMTP_HOST:
            logger.info("[email:dev] would send to=%s subject=%s", to, subject)
            logger.info("[email:dev] %s", text_body or html_body[:400])
            return True

        try:
            import aiosmtplib
            from email.message import EmailMessage

            message = EmailMessage()
            message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM}>"
            message["To"] = to
            message["Subject"] = subject
            if text_body:
                message.set_content(text_body)
            message.add_alternative(html_body, subtype="html")

            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME or None,
                password=settings.SMTP_PASSWORD or None,
                start_tls=True,
            )
            return True
        except Exception as exc:
            logger.exception("Failed to send email: %s", exc)
            return False


email_service = EmailService()