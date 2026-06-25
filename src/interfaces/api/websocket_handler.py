"""
WebSocket handler — /ws/session/{session_id}

Handles realtime bidirectional communication for a session.

Protocol:
  Client → Server:  { "type": "message", "content": "...", "user_id": "...", "agent_id": "..." }
  Client → Server:  { "type": "audio_request", "text": "...", "agent_id": "..." }
  Client → Server:  { "type": "ping" }
  Server → Client:  { "event": "message.created", "data": { ... } }
  Server → Client:  { "event": "audio.chunk", "data": { "audio_b64": "..." } }
  Server → Client:  { "event": "error", "data": { "detail": "..." } }
  Server → Client:  { "event": "pong", "data": {} }
"""
from __future__ import annotations

import base64
import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from src.application.dtos.message_dtos import SendMessageInputDTO
from src.application.use_cases.send_message import SendMessageUseCase
from src.application.use_cases.stream_audio import StreamAudioInputDTO, StreamAudioUseCase
from src.infrastructure.services.websocket_realtime_publisher import ConnectionRegistry
from src.interfaces.api.container import (
    get_connection_registry,
    get_send_message_use_case,
    get_stream_audio_use_case,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/session/{session_id}")
async def websocket_session_handler(
    session_id: str,
    websocket: WebSocket,
    registry: ConnectionRegistry = Depends(get_connection_registry),
    send_message_use_case: SendMessageUseCase = Depends(get_send_message_use_case),
    stream_audio_use_case: StreamAudioUseCase = Depends(get_stream_audio_use_case),
) -> None:
    """
    WebSocket endpoint for realtime session communication.

    Clients connect, subscribe to the session channel, and exchange
    messages in real-time. The handler delegates all business logic
    to use cases.
    """
    await websocket.accept()
    channel = f"session:{session_id}"
    registry.subscribe(channel, websocket)
    logger.info("WebSocket connected: session=%s", session_id)

    try:
        await websocket.send_text(
            json.dumps({
                "event": "connected",
                "data": {"session_id": session_id},
            })
        )

        while True:
            raw = await websocket.receive_text()

            try:
                payload: dict[str, Any] = json.loads(raw)
            except json.JSONDecodeError:
                await _send_error(websocket, "Invalid JSON payload")
                continue

            msg_type = payload.get("type")

            # ── ping/pong ─────────────────────────────────────────────────
            if msg_type == "ping":
                await websocket.send_text(json.dumps({"event": "pong", "data": {}}))
                continue

            # ── text message ──────────────────────────────────────────────
            if msg_type == "message":
                user_id = payload.get("user_id", "")
                content = payload.get("content", "")
                if not user_id or not content:
                    await _send_error(websocket, "user_id and content are required")
                    continue
                try:
                    dto = SendMessageInputDTO(
                        session_id=session_id,
                        user_id=user_id,
                        content=content,
                        synthesise_voice=bool(payload.get("synthesise_voice", False)),
                    )
                    result = await send_message_use_case.execute(dto)
                    # The use case already publishes via the realtime publisher;
                    # we also echo back directly to this connection.
                    await websocket.send_text(
                        json.dumps({
                            "event": "message.sent",
                            "data": {
                                "message_id": result.message_id,
                                "role": result.role,
                                "content": result.content,
                                "audio_url": result.audio_url,
                            },
                        })
                    )
                except Exception as exc:
                    await _send_error(websocket, str(exc))
                continue

            # ── audio streaming request ───────────────────────────────────
            if msg_type == "audio_request":
                agent_id = payload.get("agent_id", "")
                text = payload.get("text", "")
                if not agent_id or not text:
                    await _send_error(websocket, "agent_id and text are required")
                    continue
                try:
                    audio_dto = StreamAudioInputDTO(agent_id=agent_id, text=text)
                    audio_result = await stream_audio_use_case.execute(audio_dto)
                    audio_b64 = base64.b64encode(audio_result.audio_bytes).decode()
                    await websocket.send_text(
                        json.dumps({
                            "event": "audio.chunk",
                            "data": {
                                "audio_b64": audio_b64,
                                "voice_id": audio_result.voice_id,
                                "model_id": audio_result.model_id,
                            },
                        })
                    )
                except Exception as exc:
                    await _send_error(websocket, str(exc))
                continue

            await _send_error(websocket, f"Unknown message type: '{msg_type}'")

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: session=%s", session_id)
    except Exception as exc:
        logger.exception("Unexpected WebSocket error on session=%s: %s", session_id, exc)
    finally:
        registry.unsubscribe(channel, websocket)


async def _send_error(ws: WebSocket, detail: str) -> None:
    try:
        await ws.send_text(json.dumps({"event": "error", "data": {"detail": detail}}))
    except Exception:
        pass
