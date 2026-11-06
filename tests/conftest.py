"""Fixtures shared by the tests."""

import json
import logging
from collections.abc import Callable, Iterator
from typing import Any

import pytest

from project_name.logging_config import configure_logging

ReadJsonLines = Callable[[], list[dict[str, Any]]]
StartJsonLogging = Callable[..., ReadJsonLines]

RESTORED_LOGGERS = (None, "uvicorn", "uvicorn.error", "uvicorn.access")


@pytest.fixture(autouse=True)
def restored_loggers() -> Iterator[None]:
    """Put the root and uvicorn loggers back as they were, so no test affects another."""
    loggers = [logging.getLogger(name) for name in RESTORED_LOGGERS]
    states = [(logger.handlers[:], logger.level, logger.propagate) for logger in loggers]
    yield
    for logger, (handlers, level, propagate) in zip(loggers, states, strict=True):
        logger.handlers[:] = handlers
        logger.setLevel(level)
        logger.propagate = propagate


@pytest.fixture
def start_json_logging(capsys: pytest.CaptureFixture[str]) -> StartJsonLogging:
    """Return a function that configures JSON logging and gives back a reader of the lines.

    A test calls it first: pytest replaces sys.stdout between a fixture and the test, and the
    handler keeps the stream it receives, so it must be created during the test itself.

    The reader also requires an empty stderr: when a handler fails, the logging module does not
    raise, it writes "--- Logging error ---" on stderr and carries on.
    """

    def start(level: str = "INFO") -> ReadJsonLines:
        configure_logging(level, "json")

        def read_lines() -> list[dict[str, Any]]:
            captured = capsys.readouterr()
            assert captured.err == ""
            return [json.loads(line) for line in captured.out.splitlines()]

        return read_lines

    return start
