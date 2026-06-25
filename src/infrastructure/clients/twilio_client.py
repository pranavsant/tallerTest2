"""
TwilioClient — thin wrapper around the Twilio Python SDK.
"""
from __future__ import annotations

from functools import lru_cache

from twilio.rest import Client as TwilioRestClient

from src.infrastructure.config import get_settings


@lru_cache(maxsize=1)
def get_twilio_client() -> TwilioRestClient:
    """Return a shared Twilio REST client."""
    settings = get_settings()
    return TwilioRestClient(
        settings.twilio_account_sid,
        settings.twilio_auth_token,
    )
