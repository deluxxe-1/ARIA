from typing import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.settings import Settings


class ApiKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        super().__init__(app)
        self._enabled = bool(settings.enable_api_key and settings.api_key)
        self._api_key = settings.api_key or ""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if not self._enabled:
            return await call_next(request)

        path = request.url.path or ""
        if path == "/health":
            return await call_next(request)
        if path.startswith("/health/"):
            return await call_next(request)

        incoming = request.headers.get("X-ARIA-Key") or request.headers.get("X-Aria-Key")
        if incoming and incoming == self._api_key:
            return await call_next(request)

        return JSONResponse(status_code=401, content={"detail": "API key invalida."})
