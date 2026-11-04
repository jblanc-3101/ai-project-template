"""Tests for the HTTP API."""

from collections.abc import Iterator
from importlib.metadata import version

import pytest
from fastapi.testclient import TestClient

from project_name.api import app
from project_name.config import Settings, get_settings

client = TestClient(app)


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
