"""
ElevenLabsVoiceService

Implements IVoiceService using the ElevenLabs Python SDK.
Maps SDK responses into plain bytes; infrastructure errors are re-raised
as RuntimeError so the application layer stays SDK-agnostic.
"""
from __future__ import annotations

import io

from elevenlabs.client import AsyncElevenLabs
from elevenlabs.types import VoiceSettings as ELVoiceSettings

from src.application.ports.voice_service import IVoiceService
from src.domain.value_objects.voice_settings import VoiceSettings


class ElevenLabsVoiceService(IVoiceService):
    """Adapter for ElevenLabs text-to-speech synthesis."""

    def __init__(self, client: AsyncElevenLabs) -> None:
        self._client = client

    async def synthesise(self, text: str, settings: VoiceSettings) -> bytes:
        """Convert text to MP3 bytes via ElevenLabs."""
        try:
            audio_stream = await self._client.generate(
                text=text,
                voice=settings.voice_id,
                model=settings.model_id,
                voice_settings=ELVoiceSettings(
                    stability=settings.stability,
                    similarity_boost=settings.similarity_boost,
                    style=settings.style,
                    use_speaker_boost=settings.use_speaker_boost,
                ),
            )
            buffer = io.BytesIO()
            async for chunk in audio_stream:
                buffer.write(chunk)
            return buffer.getvalue()
        except Exception as exc:
            raise RuntimeError(
                f"ElevenLabs synthesis failed: {exc}"
            ) from exc

    async def synthesise_to_url(
        self,
        text: str,
        settings: VoiceSettings,
        object_key: str,
    ) -> str:
        """
        Synthesise and store the audio, returning a public URL.

        In a production deployment this would upload to Supabase Storage or S3.
        This implementation returns a placeholder URL.
        """
        _audio_bytes = await self.synthesise(text, settings)
        # TODO: upload _audio_bytes to object storage and return the public URL
        return f"https://storage.example.com/audio/{object_key}.mp3"
