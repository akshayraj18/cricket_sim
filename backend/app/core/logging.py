"""Structured (JSON) logging for the API.

Every log record is emitted as a single JSON line so it can be ingested by any
log aggregator in production while still being greppable in dev. The
request-logging middleware (see `app.core.middleware`) attaches a per-request
`request_id` via a contextvar so all logs for one request can be correlated.
"""
import json
import logging
import sys
from contextvars import ContextVar

# Set per-request by the logging middleware; included on every record so logs
# for a single request can be grouped.
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)

# Standard LogRecord attributes we don't want to duplicate into the JSON `extra`.
_RESERVED = set(
    logging.makeLogRecord({}).__dict__.keys()
) | {"message", "asctime", "taskName"}


class JsonFormatter(logging.Formatter):
    """Render a LogRecord as a compact JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        rid = request_id_ctx.get()
        if rid:
            payload["request_id"] = rid

        # Anything passed via logger.info(..., extra={...}) lands as record
        # attributes — surface those at the top level.
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    """Install the JSON formatter on the root logger (idempotent).

    Also quiets uvicorn's own access logger — the request-logging middleware
    emits a richer, structured equivalent, so the duplicate plain-text line
    would just be noise.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # uvicorn.access duplicates what our middleware logs; silence it.
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = False
