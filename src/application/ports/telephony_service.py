"""
ITelephonyService — application port for outbound calls and telephony.

Implemented in infrastructure by TwilioTelephonyService.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class OutboundCallResult:
    twilio_call_sid: str
    status: str


class ITelephonyService(ABC):
    """Abstraction over a telephony provider (Twilio)."""

    @abstractmethod
    async def initiate_call(
        self,
        to: str,
        from_: str,
        twiml_url: str,
    ) -> OutboundCallResult:
        """
        Dial a number and return the provider call SID.

        Args:
            to:        E.164 destination number.
            from_:     E.164 originating number.
            twiml_url: URL that Twilio will fetch for call instructions.

        Returns:
            OutboundCallResult with the Twilio call SID.
        """
        ...

    @abstractmethod
    async def terminate_call(self, twilio_call_sid: str) -> None:
        """Hang up an in-progress call."""
        ...
