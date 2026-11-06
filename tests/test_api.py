"""Tests for the HTTP API."""

import logging
from collections.abc import Iterator
from importlib.metadata import version
from typing import Any

import pytest
import structlog
from conftest import StartJsonLogging
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient

from project_name.api import RequestLoggingMiddleware, app
from project_name.config import Settings, get_settings

client = TestClient(app)

# A separate application, so that the routes needed by these tests stay out of the real one.
middleware_app = FastAPI()
middleware_app.add_middleware(RequestLoggingMiddleware)
middleware_client = TestClient(middleware_app)


@middleware_app.get("/write-logs")
def write_logs() -> None:
    structlog.get_logger("test.route").info("from_structlog")
    logging.getLogger("test.route").info("from_logging")


@middleware_app.get("/fail")
def fail() -> None:
    raise ValueError("failure detail")


@middleware_app.get("/fail-while-streaming")
def fail_while_streaming() -> StreamingResponse:
    def chunks() -> Iterator[bytes]:
        yield b"first chunk"
        raise ValueError("failure detail")

    return StreamingResponse(chunks())


@middleware_app.post("/read-body")
async def read_body(request: Request) -> None:
    await request.body()


@middleware_app.post("/read-body-then-fail")
async def read_body_then_fail(request: Request) -> None:
    body = await request.body()
    raise ValueError(f"body of {len(body)} bytes")


def request_lines(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the lines of the middleware: the test client also writes its own."""
    return [line for line in lines if line["logger"] == "project_name.api"]


@pytest.fixture(autouse=True)
def injected_settings() -> Iterator[None]:
    """Inject settings in every test, so that no test reads the .env file."""
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None, app_env="test")
    yield
    app.dependency_overrides.clear()


def test_health_returns_expected_json() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": version("project-name"),
        "environment": "test",
    }


@pytest.mark.parametrize("app_env", ["dev", "prod"])
def test_health_environment_follows_injected_settings(app_env: str) -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None, app_env=app_env)

    response = client.get("/health")

    assert response.json()["environment"] == app_env


def test_unknown_route_returns_404() -> None:
    response = client.get("/unknown")

    assert response.status_code == 404


def test_lifespan_events_pass_through_the_middleware() -> None:
    with TestClient(app) as lifespan_client:
        response = lifespan_client.get("/health")

    assert response.status_code == 200


def test_health_writes_one_request_line(start_json_logging: StartJsonLogging) -> None:
    read_lines = start_json_logging()

    response = client.get("/health")

    (line,) = request_lines(read_lines())
    assert set(line) == {
        "timestamp",
        "level",
        "logger",
        "event",
        "request_id",
        "method",
        "path",
        "status_code",
        "duration_ms",
    }
    assert line["event"] == "request_finished"
    assert line["level"] == "info"
    assert line["method"] == "GET"
    assert line["path"] == "/health"
    assert line["status_code"] == 200
    assert line["duration_ms"] >= 0
    assert line["duration_ms"] == round(line["duration_ms"], 2)
    assert line["request_id"] == response.headers["X-Request-ID"]


def test_two_requests_get_different_identifiers() -> None:
    first = client.get("/health")
    second = client.get("/health")

    assert first.headers["X-Request-ID"] != second.headers["X-Request-ID"]


def test_identifier_sent_by_the_client_is_ignored() -> None:
    response = client.get("/health", headers={"X-Request-ID": "chosen-by-client"})

    assert response.headers["X-Request-ID"] != "chosen-by-client"


def test_lines_written_in_a_route_carry_the_identifier(
    start_json_logging: StartJsonLogging,
) -> None:
    read_lines = start_json_logging()

    response = middleware_client.get("/write-logs")

    lines = {line["event"]: line for line in read_lines()}
    request_id = response.headers["X-Request-ID"]
    assert lines["from_structlog"]["request_id"] == request_id
    assert lines["from_logging"]["request_id"] == request_id


def test_exception_gives_a_500_and_one_error_line(start_json_logging: StartJsonLogging) -> None:
    read_lines = start_json_logging()

    response = middleware_client.get("/fail")

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}
    (line,) = request_lines(read_lines())
    assert line["event"] == "request_failed"
    assert line["level"] == "error"
    assert line["method"] == "GET"
    assert line["path"] == "/fail"
    assert line["status_code"] == 500
    assert line["duration_ms"] >= 0
    assert line["request_id"] == response.headers["X-Request-ID"]
    assert "ValueError: failure detail" in line["exception"]


def test_exception_after_response_start_is_logged_and_raised(
    start_json_logging: StartJsonLogging,
) -> None:
    read_lines = start_json_logging()

    with pytest.raises(ValueError, match="failure detail"):
        middleware_client.get("/fail-while-streaming")

    (line,) = request_lines(read_lines())
    assert line["event"] == "request_failed"
    assert line["status_code"] == 200
    assert "ValueError: failure detail" in line["exception"]


@pytest.mark.parametrize("path", ["/read-body", "/read-body-then-fail"])
def test_headers_body_and_query_string_are_not_logged(
    path: str, start_json_logging: StartJsonLogging
) -> None:
    read_lines = start_json_logging()

    middleware_client.post(
        path,
        params={"token": "fake-query-value"},
        headers={"Authorization": "Bearer fake-header-value"},
        content="fake-body-value",
    )

    (line,) = request_lines(read_lines())
    assert line["path"] == path
    output = str(line)
    assert "fake-query-value" not in output
    assert "fake-header-value" not in output
    assert "fake-body-value" not in output
