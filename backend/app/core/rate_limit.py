"""Lightweight Redis-backed fixed-window rate limiting.

Used to blunt credential/token abuse against the auth endpoints. The counter
lives in Redis so the limit holds across multiple app instances; if Redis is
unreachable we fail open (allow the request) rather than locking everyone out
over an infra blip — availability beats a hard cap for a game backend.

This is application-level throttling, not DDoS protection: volumetric network
attacks are absorbed upstream by a CDN/WAF/reverse proxy.
"""

import time

from fastapi import HTTPException, Request, status

from app.core.config import settings
from app.db.redis import get_redis


def _client_id(request: Request) -> str:
    """Best-effort client identity. Honors X-Forwarded-For (we sit behind a
    proxy in production) and falls back to the socket peer."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _window() -> int:
    """The current fixed-window bucket.

    A counter lives under one window and expires with it, so a burst that
    straddles a rollover can briefly get up to 2x the limit. That is inherent
    to fixed-window limiting and accepted here — the point is to blunt abuse,
    not to meter precisely.

    Factored out so tests can pin the window. Without that a test that sends
    N+1 requests is a coin flip near :00, which is exactly how it failed in CI
    at 04:44:00.
    """
    return int(time.time() // 60)


async def _check(request: Request, bucket: str, limit_per_minute: int) -> None:
    if not settings.rate_limit_enabled or limit_per_minute <= 0:
        return

    window = _window()
    key = f"ratelimit:{bucket}:{_client_id(request)}:{window}"
    try:
        redis = get_redis()
        count = await redis.incr(key)
        if count == 1:
            # First hit in this window — expire the counter just after the
            # window closes so keys don't accumulate.
            await redis.expire(key, 65)
    except Exception:
        # Redis down / unreachable: don't block legitimate traffic.
        return

    if count > limit_per_minute:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please slow down and try again shortly.",
            headers={"Retry-After": "60"},
        )


def rate_limit(bucket: str, limit_per_minute: int | None = None):
    """Build a FastAPI dependency that rate-limits a route by client + bucket.

    `bucket` namespaces the counter (so e.g. all auth routes can share one
    budget, or each can have its own). `limit_per_minute` defaults to the
    configured auth limit.
    """

    async def dependency(request: Request) -> None:
        await _check(request, bucket, limit_per_minute or settings.auth_rate_limit_per_minute)

    return dependency
