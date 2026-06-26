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
    CallNotFoundError,
    DomainException,
    InvalidPhoneNumberError,
    SessionNotActiveError,
    SessionNotFoundError,
)
from src.infrastructure.config import get_settings
from src.infrastructure.db import close_db, init_db
from src.infrastructure.logging import configure_logging
from src.interfaces.api.core.dependencies import get_current_user
from src.interfaces.api.routers import agents, calls, health, messages, sessions
from src.interfaces.api.websocket_handler import router as ws_router

logger = logging.getLogger(__name__)

settings = get_settings()


# ── Lifespan ──────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan handler.

    Startup
    -------
    1. Configure structured logging (structlog → stdlib bridge).
    2. Initialise the async database connection pool.

    Shutdown
    --------
    1. Dispose of the database pool, closing all open connections.
    """
    # ── Startup ───────────────────────────────────────────────────────────
    configure_logging()
    logger.info(
        "Starting Overseer AI API",
        extra={"env": settings.app_env, "version": "0.1.0"},
    )
    await init_db()

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────
    logger.info("Shutting down Overseer AI API")
    await close_db()


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
    # Calls mixes protected endpoints with public Twilio webhooks, so auth is
    # applied per-endpoint within that router rather than router-wide.
    app.include_router(calls.router, prefix="/calls", tags=["calls"])

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

    @app.exception_handler(DomainException)
    async def domain_exception_handler(
        _req: object, exc: DomainException
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": exc.message})

    return app


app = create_app()
