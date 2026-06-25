"""
VoiceSettings value object.

Carries ElevenLabs synthesis configuration — immutable and equality-by-value.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VoiceSettings:
    """
    Immutable configuration for voice synthesis.

    Attributes:
        voice_id:       ElevenLabs voice identifier.
        model_id:       ElevenLabs model identifier.
        stability:      Stability slider (0.0–1.0).
        similarity_boost: Similarity boost (0.0–1.0).
        style:          Style exaggeration (0.0–1.0).
        use_speaker_boost: Whether to apply speaker boost.
    """

    voice_id: str
    model_id: str = "eleven_turbo_v2"
    stability: float = 0.5
    similarity_boost: float = 0.75
    style: float = 0.0
    use_speaker_boost: bool = True

    def __post_init__(self) -> None:
        for field_name, val in [
            ("stability", self.stability),
            ("similarity_boost", self.similarity_boost),
            ("style", self.style),
        ]:
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"VoiceSettings.{field_name} must be between 0.0 and 1.0")

    def with_stability(self, stability: float) -> "VoiceSettings":
        return VoiceSettings(
            voice_id=self.voice_id,
            model_id=self.model_id,
            stability=stability,
            similarity_boost=self.similarity_boost,
            style=self.style,
            use_speaker_boost=self.use_speaker_boost,
        )
