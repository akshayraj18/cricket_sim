"""Request logging + the catch-all exception handler.

These build a tiny standalone app with the same observability wiring as the
real app, plus a route that raises, so we can assert the 500 handler returns a
clean JSON body (with a request id) and that the X-Request-ID header round-trips
— without needing a route in the real app that deliberately blows up.
"""
import json

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.logging import JsonFormatter, request_id_ctx
from app.core.middleware import install_observability


def _make_app() -> FastAPI:
    app = FastAPI()
    install_observability(app)

    @app.get("/ok")
    async def ok():
        return {"ok": True}

    @app.get("/boom")
    async def boom():
        raise RuntimeError("kaboom")

    return app


@pytest.fixture
async def obs_client():
    app = _make_app()
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def test_request_id_header_is_returned(obs_client):
    resp = await obs_client.get("/ok")
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-ID")


async def test_inbound_request_id_is_echoed(obs_client):
    resp = await obs_client.get("/ok", headers={"X-Request-ID": "client-supplied-id"})
    assert resp.headers.get("X-Request-ID") == "client-supplied-id"


async def test_unhandled_error_returns_clean_json_500(obs_client):
    resp = await obs_client.get("/boom")
    assert resp.status_code == 500
    body = resp.json()
    assert body["detail"] == "Internal server error"
    # The 500 body carries a request id so it can be traced back to the logs.
    assert "request_id" in body
    # No traceback leaks to the client.
    assert "kaboom" not in resp.text


def test_json_formatter_emits_structured_line_with_request_id():
    import logging

    request_id_ctx.set("test-rid-123")
    record = logging.LogRecord(
        name="app.request", level=logging.INFO, pathname=__file__, lineno=1,
        msg="request", args=(), exc_info=None,
    )
    record.method = "GET"
    record.path = "/health"
    record.status = 200
    record.latency_ms = 1.2

    line = json.loads(JsonFormatter().format(record))
    assert line["level"] == "info"
    assert line["message"] == "request"
    assert line["request_id"] == "test-rid-123"
    assert line["method"] == "GET"
    assert line["status"] == 200
    assert line["latency_ms"] == 1.2
