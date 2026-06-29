"""
Overseer AI — FastAPI application entry point.

Start with:
    uvicorn src.interfaces.api.main:app --reload --port 8000
"""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.domain.exceptions import (
    AgentNotFoundError,
    AuthorizationError,
    CallNotFoundError,
    DomainException,
    FeedNotFoundError,
    InvalidFeedNameError,
    InvalidFeedSourceTypeError,
    InvalidFeedUrlError,
    InvalidPhoneNumberError,
    InvalidPollingIntervalError,
    SessionNotActiveError,
    SessionNotFoundError,
    UserNotFoundError,
)
from src.domain.value_objects.role import Role
from src.infrastructure.config import get_settings
from src.infrastructure.db import close_db, init_db
from src.infrastructure.logging import configure_logging
from src.interfaces.api.core.dependencies import get_current_user, require_role
from src.interfaces.api.routers import (
    admin,
    agents,
    calls,
    feeds,
    health,
    messages,
    sessions,
)
from src.interfaces.api.websocket_handler import router as ws_router

logger = logging.getLogger(__name__)

settings = get_settings()


# ── Lifespan ──────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan handler.

    Startup
    -------
    1. Configure structured logging (structlog → stdlib bridge).
    2. Initialise the async database connection pool.
    3. Start the background feed-ingestion scheduler.

    Shutdown
    --------
    1. Stop the feed-ingestion scheduler.
    2. Dispose of the database pool, closing all open connections.
    """
    # ── Startup ───────────────────────────────────────────────────────────
    configure_logging()
    logger.info(
        "Starting Overseer AI API",
        extra={"env": settings.app_env, "version": "0.1.0"},
    )
    await init_db()
    app.state.feed_scheduler = await _start_feed_scheduler()

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────
    logger.info("Shutting down Overseer AI API")
    scheduler = getattr(app.state, "feed_scheduler", None)
    if scheduler is not None:
        scheduler.shutdown()
    await close_db()


async def _start_feed_scheduler() -> object | None:
    """Build and start the feed-ingestion scheduler, if enabled.

    Failures are logged and swallowed (mirroring ``init_db``) so the API still
    serves requests in environments without a reachable database/Supabase.
    """
    if not settings.feed_ingestion_enabled:
        logger.info("Feed ingestion scheduler disabled by configuration")
        return None
    try:
        # Imported lazily so the container (and its infrastructure imports) is
        # only loaded when the worker is actually enabled.
        from src.interfaces.api.container import build_feed_ingestion_scheduler

        scheduler = await build_feed_ingestion_scheduler()
        scheduler.start()
        return scheduler
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Feed ingestion scheduler could not start: %s — continuing without it.",
            exc,
        )
        return None


# ── Application factory ───────────────────────────────────────────────────────


def create_app() -> FastAPI:
    app = FastAPI(
        title="Overseer AI",
        description="AI-powered oversight and monitoring platform",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────
    # Public routers: health probe and the WebSocket handler.
    app.include_router(health.router, tags=["health"])
    app.include_router(ws_router, tags=["websocket"])

    # Protected routers: every endpoint requires a valid Supabase JWT.
    # The dependency is attached at the router level so no protected
    # endpoint can be added without authentication.
    protected = [Depends(get_current_user)]
    app.include_router(
        agents.router, prefix="/agents", tags=["agents"], dependencies=protected
    )
    app.include_router(
        sessions.router, prefix="/sessions", tags=["sessions"], dependencies=protected
    )
    app.include_router(
        messages.router, prefix="/messages", tags=["messages"], dependencies=protected
    )
    # Feeds: reads open to any authenticated user, writes gated on admin
    # per-endpoint within the router (acceptance criterion 4).
    app.include_router(
        feeds.router, prefix="/feeds", tags=["feeds"], dependencies=protected
    )
    # Calls mixes protected endpoints with public Twilio webhooks, so auth is
    # applied per-endpoint within that router rather than router-wide.
    app.include_router(calls.router, prefix="/calls", tags=["calls"])

    # Admin: user & role management. Gated router-wide on the admin role, so no
    # endpoint here is reachable without it (acceptance criterion 4).
    app.include_router(
        admin.router,
        prefix="/admin",
        tags=["admin"],
        dependencies=[Depends(require_role(Role.ADMIN))],
    )

    # ── Domain exception handlers ─────────────────────────────────────────
    @app.exception_handler(AgentNotFoundError)
    async def agent_not_found_handler(
        _req: object, exc: AgentNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": exc.message})

    @app.exception_handler(SessionNotFoundError)
    async def session_not_found_handler(
        _req: object, exc: SessionNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": exc.message})

    @app.exception_handler(CallNotFoundError)
    async def call_not_found_handler(
        _req: object, exc: CallNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": exc.message})

    @app.exception_handler(UserNotFoundError)
    async def user_not_found_handler(
        _req: object, exc: UserNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": exc.message})

    @app.exception_handler(FeedNotFoundError)
    async def feed_not_found_handler(
        _req: object, exc: FeedNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": exc.message})

    @app.exception_handler(SessionNotActiveError)
    async def session_not_active_handler(
        _req: object, exc: SessionNotActiveError
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": exc.message})

    @app.exception_handler(InvalidPhoneNumberError)
    async def invalid_phone_handler(
        _req: object, exc: InvalidPhoneNumberError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": exc.message})

    # Feed input-validation failures map to 422, mirroring the phone-number
    # handler above. These can be raised by the entity even after Pydantic
    # passes (e.g. an endpoint URL required by the chosen source type).
    @app.exception_handler(InvalidFeedNameError)
    async def invalid_feed_name_handler(
        _req: object, exc: InvalidFeedNameError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": exc.message})

    @app.exception_handler(InvalidFeedSourceTypeError)
    async def invalid_feed_source_type_handler(
        _req: object, exc: InvalidFeedSourceTypeError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": exc.message})

    @app.exception_handler(InvalidFeedUrlError)
    async def invalid_feed_url_handler(
        _req: object, exc: InvalidFeedUrlError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": exc.message})

    @app.exception_handler(InvalidPollingIntervalError)
    async def invalid_polling_interval_handler(
        _req: object, exc: InvalidPollingIntervalError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": exc.message})

    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(
        _req: object, exc: AuthorizationError
    ) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": exc.message})

    @app.exception_handler(DomainException)
    async def domain_exception_handler(
        _req: object, exc: DomainException
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": exc.message})

    return app


app = create_app()
