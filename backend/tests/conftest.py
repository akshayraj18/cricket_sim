import pytest
from httpx import ASGITransport, AsyncClient
from redis.asyncio import from_url
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.redis import get_redis
from app.db.session import get_db
from app.main import app

TEST_REDIS_URL = settings.redis_url.rsplit("/", 1)[0] + "/15"


@pytest.fixture
async def client():
    """An AsyncClient for the app, with auth/career tables and the test Redis DB cleared afterwards.

    Uses its own NullPool engine so connections aren't reused across the
    different event loops that pytest-asyncio creates per test, and a
    separate Redis logical DB (15) so live-match cache keys don't collide
    with development data.
    """
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    redis = from_url(TEST_REDIS_URL)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    def override_get_redis():
        return redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()
        async with engine.begin() as conn:
            await conn.execute(text("TRUNCATE TABLE refresh_tokens, careers, users CASCADE"))
        await engine.dispose()
        await redis.flushdb()
        await redis.aclose()


@pytest.fixture
async def auth_headers(client: AsyncClient):
    """Bearer auth headers for a fresh guest user."""
    resp = await client.post("/auth/guest")
    access_token = resp.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def db_session(client: AsyncClient):
    """A standalone DB session against the same database the `client` fixture uses.

    For asserting on rows (e.g. `matches`/`match_balls`) that aren't yet
    exposed over HTTP.
    """
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()
