"""Smoke tests: the package is installed and importable."""

from importlib.metadata import version

import project_name


def test_package_imports() -> None:
    assert project_name.__name__ == "project_name"


def test_package_has_version() -> None:
    assert version("project-name") != ""
