"""HTTP API of the project."""

from importlib.metadata import metadata
from typing import Annotated, Literal

from fastapi import Depends, FastAPI
from pydantic import BaseModel

from project_name.config import AppEnv, Settings, get_settings

PACKAGE_METADATA = metadata("project-name")

app = FastAPI(title=PACKAGE_METADATA["Name"], version=PACKAGE_METADATA["Version"])


class HealthResponse(BaseModel):
    """Body of the /health response."""

    status: Literal["ok"]
    version: str
    environment: AppEnv


@app.get("/health")
def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    """Report that the API is running, with its version and environment."""
    return HealthResponse(status="ok", version=app.version, environment=settings.app_env)
