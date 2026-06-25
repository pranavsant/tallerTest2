"""
IRealtimePublisher — application port for WebSocket / realtime event publishing.

Implemented in infrastructure by WebSocketRealtimePublisher.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IRealtimePublisher(ABC):
    """Abstraction over a realtime messaging channel (WebSockets, SSE, etc.)."""

    @abstractmethod
    async def publish(
        self,
        channel: str,
        event: str,
        payload: dict[str, Any],
    ) -> None:
        """
        Publish an event to a named channel.

        Args:
            channel: e.g. "session:{session_id}"
            event:   e.g. "message.created", "session.started"
            payload: JSON-serialisable dict.
        """
        ...

    @abstractmethod
    async def broadcast(
        self,
        event: str,
        payload: dict[str, Any],
    ) -> None:
        """Broadcast an event to all connected subscribers."""
        ...
