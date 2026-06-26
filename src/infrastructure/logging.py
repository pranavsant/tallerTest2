"""
Structured logging configuration using structlog.

Call ``configure_logging()`` once at application startup (inside the lifespan
handler) to install JSON rendering for production and coloured console output
for development.

All standard-library ``logging.getLogger(...)`` calls are automatically
bridged into structlog via ``structlog.stdlib.ProcessorFormatter``, so existing
``logger.info(...)`` calls throughout the codebase gain structured context
without any changes.

Usage
-----
    from src.infrastructure.logging import configure_logging
    configure_logging()          # reads APP_ENV from settings
"""
from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

from src.infrastructure.config import get_settings


def configure_logging() -> None:
    """
    Configure structlog + stdlib logging.

    * Production  → JSON renderer (one compact JSON line per record).
    * Development → ConsoleRenderer (coloured, human-readable output).
    """
    settings = get_settings()
    is_production = settings.is_production

    # Shared processors run on every log record regardless of renderer.
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]

    if is_production:
        # stdlib → structlog bridge uses JSONRenderer.
        renderer: Any = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        # foreign_pre_chain handles records that arrive from plain stdlib loggers
        # (i.e. third-party libraries that don't use structlog directly).
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    # Remove any handlers that were added before configure_logging() ran
    # (e.g. by uvicorn's default setup) to avoid duplicate output.
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG if not is_production else logging.INFO)

    # Quieten noisy third-party loggers.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if not is_production else logging.WARNING
    )
