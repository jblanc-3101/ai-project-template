"""Structured logging: one event per line on standard output, in JSON or for the console."""

import logging
import sys

import structlog
from structlog.typing import Processor

from project_name.config import LogFormat

# Uvicorn installs its own handlers on these loggers before the application is imported.
UVICORN_LOGGERS = ("uvicorn", "uvicorn.error")
UVICORN_ACCESS_LOGGER = "uvicorn.access"


def build_renderers(log_format: LogFormat) -> list[Processor]:
    """Return the last processors of the chain, which turn an event into text.

    Neither renderer shows local variables in tracebacks: they could contain secrets.
    """
    if log_format == "json":
        return [structlog.processors.format_exc_info, structlog.processors.JSONRenderer()]
    return [structlog.dev.ConsoleRenderer(exception_formatter=structlog.dev.plain_traceback)]


def configure_uvicorn_loggers() -> None:
    """Send uvicorn logs to the root logger and turn off its access log."""
    for name in UVICORN_LOGGERS:
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
        # Without this, the level set by uvicorn would take priority over the root logger's.
        logger.setLevel(logging.NOTSET)

    # Same effect as --no-access-log: with no handler, uvicorn stops writing these lines.
    access_logger = logging.getLogger(UVICORN_ACCESS_LOGGER)
    access_logger.handlers.clear()
    access_logger.propagate = False


def configure_logging(level: str, log_format: LogFormat) -> None:
    """Send structlog and standard logging events to standard output, in the same format."""
    # Applied to structlog events and to events from the standard logging module.
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                *build_renderers(log_format),
            ],
        )
    )

    root_logger = logging.getLogger()
    root_logger.handlers[:] = [handler]
    root_logger.setLevel(level)

    configure_uvicorn_loggers()
