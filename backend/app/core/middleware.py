"""Request-logging middleware and a catch-all exception handler.

The middleware assigns each request a short `request_id` (echoed back in the
`X-Request-ID` header and bound to the logging contextvar), times the request,
and logs one structured line per request. The exception handler ensures an
unhandled error is logged with its traceback and returns a clean JSON 500
(carrying the request id) instead of leaking a stack trace to the client.
"""
import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import request_id_ctx

logger = logging.getLogger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        token = request_id_ctx.set(request_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            # Logged + converted to a 500 by the exception handler below; we
            # still emit the request line so latency/path are captured.
            latency_ms = round((time.perf_counter() - start) * 1000, 1)
            logger.exception(
                "request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": 500,
                    "latency_ms": latency_ms,
                },
            )
            request_id_ctx.reset(token)
            raise

        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "latency_ms": latency_ms,
            },
        )
        response.headers["X-Request-ID"] = request_id
        request_id_ctx.reset(token)
        return response


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Last-resort handler for errors not caught by route-level handling.

    The error is already logged by the middleware; here we just return a clean
    JSON 500 that includes the request id so a user-reported error can be traced
    back to its server logs (and, once wired, its Sentry event).
    """
    logger.error("unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": request_id_ctx.get()},
    )


def install_observability(app: FastAPI) -> None:
    """Attach request logging + the catch-all exception handler to `app`."""
    app.add_middleware(RequestLoggingMiddleware)
    app.add_exception_handler(Exception, unhandled_exception_handler)
