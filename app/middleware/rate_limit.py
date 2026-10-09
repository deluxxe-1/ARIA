import asyncio
import time
from typing import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.settings import Settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        super().__init__(app)
        self._enabled = settings.enable_rate_limit
        self._max_per_minute = int(settings.rate_limit_per_minute)
        self._requests: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()

    def _client_ip(self, request: Request) -> str:
        if request.client and request.client.host:
            return request.client.host
        forwarded = request.headers.get("X-Forwarded-For") or request.headers.get("X-Real-IP")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return "unknown"

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if not self._enabled:
            return await call_next(request)

        ip = self._client_ip(request)
        now = time.monotonic()
        window_start = now - 60.0
        async with self._lock:
            timestamps = self._requests.setdefault(ip, [])
            while timestamps and timestamps[0] < window_start:
                timestamps.pop(0)
            if len(timestamps) >= self._max_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Demasiadas peticiones en poco tiempo."},
                    headers={"Retry-After": "60"},
                )
            timestamps.append(now)
        return await call_next(request)
