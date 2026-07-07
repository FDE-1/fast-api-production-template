"""Email side effects. Kept in the service layer, run off the request path."""

from __future__ import annotations

import time

from ..utils.logger import logger


def send_welcome_email(email: str) -> None:
    """Send the welcome email. Runs as a background task off the hot path."""
    time.sleep(5)
    logger.info("Email sent to {}", email)
