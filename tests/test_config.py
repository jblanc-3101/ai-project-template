"""Tests for the application settings."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from pydantic import ValidationError

from project_name.config import Settings, get_settings

SETTINGS_VARIABLES = ("APP_ENV", "LOG_LEVEL", "API_KEY")


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove settings variables so the machine's environment cannot change the results."""
    for name in SETTINGS_VARIABLES:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def empty_settings_cache() -> Iterator[None]:
    """Empty the get_settings cache before and after a test, so no test sees another's result."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_default_values() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_env == "dev"
    assert settings.log_level == "INFO"
    assert settings.api_key is None


def test_environment_variable_overrides_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "prod")

    settings = Settings(_env_file=None)

    assert settings.app_env == "prod"


def test_invalid_app_env_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "staging")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_secret_is_masked_when_displayed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "fake-value")

    settings = Settings(_env_file=None)

    assert settings.api_key is not None
    assert "fake-value" not in repr(settings)
    assert "fake-value" not in str(settings.api_key)
    assert settings.api_key.get_secret_value() == "fake-value"


@pytest.mark.usefixtures("empty_settings_cache")
def test_get_settings_returns_one_cached_object(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    first = get_settings()
    second = get_settings()

    assert isinstance(first, Settings)
    assert second is first
