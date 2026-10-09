import uuid
from contextvars import ContextVar
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logger import get_logger

REQUEST_ID_CTX: ContextVar[str] = ContextVar("request_id", default="")


class RequestIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._logger = get_logger(__name__)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        incoming = request.headers.get("X-Request-ID") or request.headers.get("X-Request-Id")
        request_id = incoming or uuid.uuid4().hex
        token = REQUEST_ID_CTX.set(request_id)
        try:
            self._logger = self._logger.bind(request_id=request_id)
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            REQUEST_ID_CTX.reset(token)
