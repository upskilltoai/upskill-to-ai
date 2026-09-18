"""Structured logging setup.

Logs are emitted as JSON in every environment except local development, where
a human-readable console renderer is easier to read. JSON matters because the
hosting platform's log viewer parses it natively — severity becomes a real
field to filter on, and any key/value attached to a log line becomes
queryable, instead of everything being one flat string.

Call `configure_logging()` once at startup, then anywhere:

    import structlog
    log = structlog.get_logger()
    log.info("capstone_submitted", learner_id=42, phase="phase1")

Note: this configures the application's own log calls. Uvicorn's access logs
still use its own plain-text format — routing those through structlog too is
deferred until deployment, when a log aggregator is actually consuming them.
"""

from __future__ import annotations

import logging

import structlog

from app.config import settings


def configure_logging() -> None:
    renderer: structlog.types.Processor = (
        structlog.dev.ConsoleRenderer()
        if settings.environment == "development"
        else structlog.processors.JSONRenderer()
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )
