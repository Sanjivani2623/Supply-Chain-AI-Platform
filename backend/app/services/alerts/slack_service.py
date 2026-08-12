"""
Slack alert delivery via incoming webhook (section 26). Refactored from
the original notebook's `send_msg()` proof-of-concept into a reusable,
config-driven, non-blocking-safe service.
"""
import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def send_slack_alert(text: str) -> bool:
    if not settings.SLACK_WEBHOOK_URL:
        logger.info("slack.disabled", msg="SLACK_WEBHOOK_URL not configured, skipping")
        return False
    try:
        resp = httpx.post(settings.SLACK_WEBHOOK_URL, json={"text": text}, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as exc:
        logger.error("slack.send_failed", error=str(exc))
        return False
