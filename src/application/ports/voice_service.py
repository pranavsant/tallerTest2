"""
IVoiceService — application port for speech synthesis.

Implemented in infrastructure by ElevenLabsVoiceService.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.value_objects.voice_settings import VoiceSettings


class IVoiceService(ABC):
    """Abstraction over a text-to-speech provider."""

    @abstractmethod
    async def synthesise(
        self,
        text: str,
        settings: VoiceSettings,
    ) -> bytes:
        """
        Convert text to audio bytes (MP3).

        Args:
            text:     The text to synthesise.
            settings: Voice configuration.

        Returns:
            Raw MP3 audio bytes.
        """
        ...

    @abstractmethod
    async def synthesise_to_url(
        self,
        text: str,
        settings: VoiceSettings,
        object_key: str,
    ) -> str:
        """
        Synthesise text and store the result, returning a public URL.

        Args:
            text:       The text to synthesise.
            settings:   Voice configuration.
            object_key: Storage key / filename.

        Returns:
            Public URL to the stored audio file.
        """
        ...
