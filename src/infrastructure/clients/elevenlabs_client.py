"""
ElevenLabsClient — thin wrapper around the ElevenLabs Python SDK.
"""
from __future__ import annotations

from functools import lru_cache

from elevenlabs.client import AsyncElevenLabs

from src.infrastructure.config import get_settings


@lru_cache(maxsize=1)
def get_elevenlabs_client() -> AsyncElevenLabs:
    """Return a shared async ElevenLabs client."""
    settings = get_settings()
    return AsyncElevenLabs(api_key=settings.elevenlabs_api_key)
