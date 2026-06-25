"""
TwilioTelephonyService

Implements ITelephonyService using the Twilio REST API.
"""
from __future__ import annotations

import asyncio
from functools import partial

from twilio.rest import Client as TwilioRestClient

from src.application.ports.telephony_service import ITelephonyService, OutboundCallResult


class TwilioTelephonyService(ITelephonyService):
    """Adapter that wraps the synchronous Twilio SDK in an async interface."""

    def __init__(self, client: TwilioRestClient) -> None:
        self._client = client

    async def initiate_call(
        self,
        to: str,
        from_: str,
        twiml_url: str,
    ) -> OutboundCallResult:
        """
        Dial out via Twilio.  The Twilio SDK is synchronous, so we run it
        in a thread-pool executor to avoid blocking the event loop.
        """
        try:
            loop = asyncio.get_running_loop()
            call = await loop.run_in_executor(
                None,
                partial(
                    self._client.calls.create,
                    to=to,
                    from_=from_,
                    url=twiml_url,
                ),
            )
            return OutboundCallResult(
                twilio_call_sid=call.sid,
                status=call.status,
            )
        except Exception as exc:
            raise RuntimeError(f"Twilio call initiation failed: {exc}") from exc

    async def terminate_call(self, twilio_call_sid: str) -> None:
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                partial(
                    self._client.calls(twilio_call_sid).update,
                    status="completed",
                ),
            )
        except Exception as exc:
            raise RuntimeError(
                f"Twilio call termination failed for SID '{twilio_call_sid}': {exc}"
            ) from exc
