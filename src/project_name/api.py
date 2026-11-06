"""HTTP API of the project."""

from importlib.metadata import metadata
from time import perf_counter
from typing import Annotated, Any, Literal
from uuid import uuid4

import structlog
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from project_name.config import AppEnv, Settings, get_settings
from project_name.logging_config import configure_logging

PACKAGE_METADATA = metadata("project-name")

# Called at import, not in the lifespan: uvicorn imports the application, writes its first log
# lines, and only then runs the lifespan. In the lifespan, those lines would keep uvicorn's
# format. Uvicorn has already set up its own logging at this point, so this call comes after it.
startup_settings = get_settings()
configure_logging(startup_settings.log_level, startup_settings.log_format)

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware:
    """Give each HTTP request an identifier and write one log line when it ends.

    Only the method and the path are read: headers, body and query string are never logged.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid4())
        started_at = perf_counter()
        status_code = 500
        response_started = False

        async def send_with_request_id(message: Message) -> None:
            nonlocal response_started, status_code
            if message["type"] == "http.response.start":
                response_started = True
                status_code = message["status"]
                message.setdefault("headers", [])
                MutableHeaders(scope=message)["X-Request-ID"] = request_id
            await send(message)

        def request_fields() -> dict[str, Any]:
            return {
                "method": scope["method"],
                "path": scope["path"],
                "status_code": status_code,
                "duration_ms": round((perf_counter() - started_at) * 1000, 2),
            }

        with structlog.contextvars.bound_contextvars(request_id=request_id):
            try:
                await self.app(scope, receive, send_with_request_id)
            except Exception:
                logger.exception("request_failed", **request_fields())
                # Once the response has started, the only way to signal the failure is to let
                # the server cut the connection.
                if response_started:
                    raise
                # Sent here, not by Starlette's outer error handler, so that the response
                # carries X-Request-ID and uvicorn does not log the same error a second time.
                response = JSONResponse({"detail": "Internal Server Error"}, status_code=500)
                await response(scope, receive, send_with_request_id)
            else:
                logger.info("request_finished", **request_fields())


app = FastAPI(title=PACKAGE_METADATA["Name"], version=PACKAGE_METADATA["Version"])
app.add_middleware(RequestLoggingMiddleware)


class HealthResponse(BaseModel):
    """Body of the /health response."""

    status: Literal["ok"]
    version: str
    environment: AppEnv


@app.get("/health")
def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    """Report that the API is running, with its version and environment."""
    return HealthResponse(status="ok", version=app.version, environment=settings.app_env)
