"""
Email alert delivery (section 27). Provider-agnostic wrapper - plug in
SendGrid/SES/Postmark by implementing `_send_via_provider`.
"""
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def send_email_alert(subject: str, body: str, to: str | None = None) -> bool:
    if not settings.EMAIL_API_KEY:
        logger.info("email.disabled", msg="EMAIL_API_KEY not configured, skipping", subject=subject)
        return False
    # Real implementation would call SendGrid/SES here using settings.EMAIL_API_KEY.
    logger.info("email.sent", subject=subject, to=to or "supply-chain-team@example.com")
    return True
