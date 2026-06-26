"""
Dependency Injection Container

Wires every layer together. Infrastructure implementations are bound to
application interfaces here — the application and domain layers never
see this file.

All FastAPI `Depends(...)` calls resolve through this module.
"""
from __future__ import annotations

from functools import lru_cache

from src.application.ports.realtime_publisher import IRealtimePublisher
from src.application.ports.telephony_service import ITelephonyService
from src.application.ports.token_validator import ITokenValidator
from src.application.ports.user_directory import IUserDirectory
from src.application.ports.voice_service import IVoiceService
from src.application.use_cases.assign_role import AssignRoleUseCase
from src.application.use_cases.create_agent import CreateAgentUseCase
from src.application.use_cases.end_session import EndSessionUseCase
from src.application.use_cases.get_agent import GetAgentUseCase
from src.application.use_cases.initiate_call import InitiateCallUseCase
from src.application.use_cases.list_agents import ListAgentsUseCase
from src.application.use_cases.list_users import ListUsersUseCase
from src.application.use_cases.send_message import SendMessageUseCase
from src.application.use_cases.set_user_active import SetUserActiveUseCase
from src.application.use_cases.start_session import StartSessionUseCase
from src.application.use_cases.stream_audio import StreamAudioUseCase
from src.domain.repositories.agent_repository import IAgentRepository
from src.domain.repositories.call_repository import ICallRepository
from src.domain.repositories.message_repository import IMessageRepository
from src.domain.repositories.session_repository import ISessionRepository
from src.domain.services.session_orchestrator import SessionOrchestrator
from src.infrastructure.clients.elevenlabs_client import get_elevenlabs_client
from src.infrastructure.clients.supabase_client import get_supabase_client
from src.infrastructure.clients.twilio_client import get_twilio_client
from src.infrastructure.config import get_settings
from src.infrastructure.repositories.supabase_agent_repository import (
    SupabaseAgentRepository,
)
from src.infrastructure.repositories.supabase_call_repository import (
    SupabaseCallRepository,
)
from src.infrastructure.repositories.supabase_message_repository import (
    SupabaseMessageRepository,
)
from src.infrastructure.repositories.supabase_session_repository import (
    SupabaseSessionRepository,
)
from src.infrastructure.services.elevenlabs_voice_service import ElevenLabsVoiceService
from src.infrastructure.services.supabase_jwt_validator import SupabaseJWTValidator
from src.infrastructure.services.supabase_user_directory import SupabaseUserDirectory
from src.infrastructure.services.twilio_telephony_service import TwilioTelephonyService
from src.infrastructure.services.websocket_realtime_publisher import (
    ConnectionRegistry,
    WebSocketRealtimePublisher,
)

# ── Singletons ────────────────────────────────────────────────────────────────

# The connection registry is a process-wide singleton shared between
# the WebSocket handler (which registers connections) and the publisher.
_connection_registry = ConnectionRegistry()


def get_connection_registry() -> ConnectionRegistry:
    return _connection_registry


# ── Repository factories ──────────────────────────────────────────────────────


async def get_agent_repository() -> IAgentRepository:
    client = await get_supabase_client()
    return SupabaseAgentRepository(client)


async def get_session_repository() -> ISessionRepository:
    client = await get_supabase_client()
    return SupabaseSessionRepository(client)


async def get_message_repository() -> IMessageRepository:
    client = await get_supabase_client()
    return SupabaseMessageRepository(client)


async def get_call_repository() -> ICallRepository:
    client = await get_supabase_client()
    return SupabaseCallRepository(client)


async def get_user_directory() -> IUserDirectory:
    client = await get_supabase_client()
    return SupabaseUserDirectory(client)


# ── Service factories ─────────────────────────────────────────────────────────


def get_voice_service() -> IVoiceService:
    return ElevenLabsVoiceService(get_elevenlabs_client())


def get_telephony_service() -> ITelephonyService:
    return TwilioTelephonyService(get_twilio_client())


def get_realtime_publisher() -> IRealtimePublisher:
    return WebSocketRealtimePublisher(_connection_registry)


def get_orchestrator() -> SessionOrchestrator:
    return SessionOrchestrator()


@lru_cache(maxsize=1)
def get_token_validator() -> ITokenValidator:
    settings = get_settings()
    return SupabaseJWTValidator(jwt_secret=settings.supabase_jwt_secret)


# ── Use case factories ────────────────────────────────────────────────────────


async def get_create_agent_use_case() -> CreateAgentUseCase:
    return CreateAgentUseCase(await get_agent_repository())


async def get_get_agent_use_case() -> GetAgentUseCase:
    return GetAgentUseCase(await get_agent_repository())


async def get_list_agents_use_case() -> ListAgentsUseCase:
    return ListAgentsUseCase(await get_agent_repository())


async def get_start_session_use_case() -> StartSessionUseCase:
    return StartSessionUseCase(
        agent_repository=await get_agent_repository(),
        session_repository=await get_session_repository(),
        orchestrator=get_orchestrator(),
        publisher=get_realtime_publisher(),
    )


async def get_end_session_use_case() -> EndSessionUseCase:
    return EndSessionUseCase(
        session_repository=await get_session_repository(),
        agent_repository=await get_agent_repository(),
        orchestrator=get_orchestrator(),
        publisher=get_realtime_publisher(),
    )


async def get_send_message_use_case() -> SendMessageUseCase:
    return SendMessageUseCase(
        session_repository=await get_session_repository(),
        message_repository=await get_message_repository(),
        agent_repository=await get_agent_repository(),
        orchestrator=get_orchestrator(),
        voice_service=get_voice_service(),
        publisher=get_realtime_publisher(),
    )


async def get_initiate_call_use_case() -> InitiateCallUseCase:
    settings = get_settings()
    return InitiateCallUseCase(
        agent_repository=await get_agent_repository(),
        call_repository=await get_call_repository(),
        telephony_service=get_telephony_service(),
        from_phone_number=settings.twilio_phone_number,
        twiml_base_url=settings.twilio_webhook_base_url,
    )


async def get_stream_audio_use_case() -> StreamAudioUseCase:
    return StreamAudioUseCase(
        agent_repository=await get_agent_repository(),
        voice_service=get_voice_service(),
    )


async def get_list_users_use_case() -> ListUsersUseCase:
    return ListUsersUseCase(await get_user_directory())


async def get_assign_role_use_case() -> AssignRoleUseCase:
    return AssignRoleUseCase(await get_user_directory())


async def get_set_user_active_use_case() -> SetUserActiveUseCase:
    return SetUserActiveUseCase(await get_user_directory())
