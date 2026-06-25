"""
WebSocketRealtimePublisher

Implements IRealtimePublisher using an in-process WebSocket connection registry.
Connections are registered and unregistered by the WebSocket handler in the
interfaces layer; this service just dispatches messages to them.
"""
from __future__ import annotations

import json
import logging
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

from src.application.ports.realtime_publisher import IRealtimePublisher

logger = logging.getLogger(__name__)


class ConnectionRegistry:
    """
    Thread-safe (asyncio-safe) registry mapping channel names → WebSocket sets.

    Injected into both the WebSocket handler (to register connections)
    and the publisher (to send messages).
    """

    def __init__(self) -> None:
        self._channels: dict[str, set[WebSocket]] = defaultdict(set)

    def subscribe(self, channel: str, ws: WebSocket) -> None:
        self._channels[channel].add(ws)

    def unsubscribe(self, channel: str, ws: WebSocket) -> None:
        self._channels[channel].discard(ws)
        if not self._channels[channel]:
            del self._channels[channel]

    def get_subscribers(self, channel: str) -> frozenset[WebSocket]:
        return frozenset(self._channels.get(channel, set()))

    def get_all_connections(self) -> frozenset[WebSocket]:
        all_ws: set[WebSocket] = set()
        for connections in self._channels.values():
            all_ws.update(connections)
        return frozenset(all_ws)


class WebSocketRealtimePublisher(IRealtimePublisher):
    """Publishes events to subscribed WebSocket connections."""

    def __init__(self, registry: ConnectionRegistry) -> None:
        self._registry = registry

    async def publish(
        self,
        channel: str,
        event: str,
        payload: dict[str, Any],
    ) -> None:
        message = json.dumps({"event": event, "data": payload})
        dead: list[WebSocket] = []

        for ws in self._registry.get_subscribers(channel):
            try:
                await ws.send_text(message)
            except Exception:
                logger.warning("Dead WebSocket detected on channel '%s', removing.", channel)
                dead.append(ws)

        for ws in dead:
            self._registry.unsubscribe(channel, ws)

    async def broadcast(self, event: str, payload: dict[str, Any]) -> None:
        message = json.dumps({"event": event, "data": payload})
        dead: list[tuple[str, WebSocket]] = []

        for channel, connections in list(self._registry._channels.items()):
            for ws in connections:
                try:
                    await ws.send_text(message)
                except Exception:
                    dead.append((channel, ws))

        for channel, ws in dead:
            self._registry.unsubscribe(channel, ws)
