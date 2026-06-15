"""The auth endpoints are rate-limited per client. This test re-enables the
limiter (the global conftest fixture disables it everywhere else) with a tiny
cap and asserts the cap is enforced, then that exceeding it returns 429."""
import pytest
from httpx import ASGITransport, AsyncClient
from redis.asyncio import from_url

from app.core import rate_limit
from app.core.config import settings
from app.db.session import get_db
from app.main import app

from .conftest import TEST_REDIS_URL


@pytest.fixture
async def limited_client(monkeypatch):
    """Like the `client` fixture but with rate limiting ON, a small cap, and the
    limiter pointed at the test Redis DB."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool

    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    redis = from_url(TEST_REDIS_URL)
    await redis.flushdb()

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    monkeypatch.setattr(settings, "auth_rate_limit_per_minute", 3)
    # The limiter calls get_redis() directly (not via DI), so point it at test Redis.
    monkeypatch.setattr(rate_limit, "get_redis", lambda: redis)

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()
        from sqlalchemy import text

        async with engine.begin() as conn:
            await conn.execute(text("TRUNCATE TABLE refresh_tokens, careers, users CASCADE"))
        await engine.dispose()
        await redis.flushdb()
        await redis.aclose()


async def test_auth_endpoint_rate_limited(limited_client):
    # Cap is 3/min. The first 3 guest creations succeed...
    for _ in range(3):
        resp = await limited_client.post("/auth/guest")
        assert resp.status_code == 200, resp.text
    # ...the 4th is throttled.
    resp = await limited_client.post("/auth/guest")
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers
