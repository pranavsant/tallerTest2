"""
Health-check router — GET /health

Returns HTTP 200 when the service is up and the database is reachable.
Returns HTTP 503 when the database probe fails (service is degraded).

Response schema
---------------
{
    "status":  "ok" | "degraded",
    "db":      "ok" | "unavailable",
    "service": "overseer-ai",
    "version": "0.1.0"
}
"""
from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text

from src.infrastructure.db import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

_VERSION = "0.1.0"
_SERVICE = "overseer-ai"


class HealthResponse(BaseModel):
    status: str
    db: str
    service: str
    version: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health check",
    description=(
        "Returns 200 when the API is running and the database is reachable. "
        "Returns 503 when the database probe fails."
    ),
)
async def health_check() -> JSONResponse:
    """
    Probe the database with a lightweight ``SELECT 1`` query.

    * On success → HTTP 200, ``{"status": "ok", "db": "ok", ...}``
    * On failure → HTTP 503, ``{"status": "degraded", "db": "unavailable", ...}``

    The DB session is obtained directly (not via ``Depends``) so that a cold
    startup where the pool is not yet ready still returns a useful response
    rather than an unhandled 500.
    """
    db_status = "unavailable"
    try:
        # get_db() is an async generator; drive it manually to avoid needing
        # a full Depends() chain (which would turn a pool absence into a 500).
        async for session in get_db():
            await session.execute(text("SELECT 1"))
            db_status = "ok"
            break
    except Exception as exc:
        logger.warning("Health check DB probe failed: %s", exc)

    overall = "ok" if db_status == "ok" else "degraded"
    http_status = 200 if overall == "ok" else 503

    body = HealthResponse(
        status=overall,
        db=db_status,
        service=_SERVICE,
        version=_VERSION,
    )
    return JSONResponse(status_code=http_status, content=body.model_dump())
