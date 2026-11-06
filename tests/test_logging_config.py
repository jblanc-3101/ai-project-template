"""Tests for the logging configuration."""

import json
import logging
import logging.config
import re
from datetime import UTC, datetime, timedelta

import pytest
import structlog
from conftest import StartJsonLogging
from uvicorn.config import LOGGING_CONFIG

from project_name.logging_config import configure_logging

ANSI_CODE = re.compile(r"\x1b\[[0-9;]*m")


def test_json_line_has_exactly_the_expected_fields(start_json_logging: StartJsonLogging) -> None:
    read_lines = start_json_logging()

    structlog.get_logger("test.logger").info("model_loaded", rows=10)

    (line,) = read_lines()
    assert set(line) == {"timestamp", "level", "logger", "event", "rows"}
    assert line["level"] == "info"
    assert line["logger"] == "test.logger"
    assert line["event"] == "model_loaded"
    assert line["rows"] == 10


def test_timestamp_is_iso_8601_in_utc(start_json_logging: StartJsonLogging) -> None:
    read_lines = start_json_logging()

    structlog.get_logger().info("event")

    (line,) = read_lines()
    timestamp = datetime.fromisoformat(line["timestamp"])
    assert timestamp.utcoffset() == timedelta(0)
    assert abs(datetime.now(UTC) - timestamp) < timedelta(minutes=1)


def test_json_error_is_one_line_with_its_traceback(start_json_logging: StartJsonLogging) -> None:
    read_lines = start_json_logging()

    try:
        raise ValueError("invalid input")
    except ValueError:
        structlog.get_logger().exception("failed")

    (line,) = read_lines()
    assert line["level"] == "error"
    assert "Traceback" in line["exception"]
    assert "ValueError: invalid input" in line["exception"]


def test_standard_logging_uses_the_same_format(start_json_logging: StartJsonLogging) -> None:
    read_lines = start_json_logging()

    logging.getLogger("some.library").warning("disk %s full", "D")

    (line,) = read_lines()
    assert set(line) == {"timestamp", "level", "logger", "event"}
    assert line["level"] == "warning"
    assert line["logger"] == "some.library"
    assert line["event"] == "disk D full"


def test_context_reaches_standard_logging(start_json_logging: StartJsonLogging) -> None:
    read_lines = start_json_logging()

    with structlog.contextvars.bound_contextvars(request_id="abc"):
        logging.getLogger("some.library").warning("event")

    (line,) = read_lines()
    assert line["request_id"] == "abc"


def test_uvicorn_logs_use_the_same_format(start_json_logging: StartJsonLogging) -> None:
    logging.config.dictConfig(LOGGING_CONFIG)
    read_lines = start_json_logging()

    logging.getLogger("uvicorn.error").info("Started server process")

    (line,) = read_lines()
    assert line["logger"] == "uvicorn.error"
    assert line["event"] == "Started server process"
    assert logging.getLogger("uvicorn").handlers == []


def test_uvicorn_access_log_is_disabled() -> None:
    logging.config.dictConfig(LOGGING_CONFIG)

    configure_logging("INFO", "json")

    assert not logging.getLogger("uvicorn.access").hasHandlers()


def test_level_applies_to_uvicorn_logs(start_json_logging: StartJsonLogging) -> None:
    logging.config.dictConfig(LOGGING_CONFIG)
    read_lines = start_json_logging("WARNING")

    logging.getLogger("uvicorn.error").info("hidden")
    logging.getLogger("uvicorn.error").warning("shown")

    (line,) = read_lines()
    assert line["event"] == "shown"


def test_level_applies_to_structlog(start_json_logging: StartJsonLogging) -> None:
    read_lines = start_json_logging("WARNING")

    structlog.get_logger().info("hidden")

    assert read_lines() == []


def test_configuring_twice_does_not_duplicate_lines(start_json_logging: StartJsonLogging) -> None:
    start_json_logging()
    read_lines = start_json_logging()

    structlog.get_logger().info("event")

    assert len(read_lines()) == 1


def test_console_format_is_readable_text(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO", "console")

    structlog.get_logger().info("model_loaded", rows=10)

    captured = capsys.readouterr()
    output = ANSI_CODE.sub("", captured.out)
    assert captured.err == ""
    assert "model_loaded" in output
    assert "rows=10" in output
    with pytest.raises(json.JSONDecodeError):
        json.loads(output)
