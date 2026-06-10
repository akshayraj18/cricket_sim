"""Cached fetch of JSON Web Key Sets (JWKS) for verifying third-party identity tokens."""
import time

import httpx

_CACHE: dict[str, tuple[float, dict]] = {}
_CACHE_TTL_SECONDS = 3600


async def get_jwks(url: str) -> dict:
    cached = _CACHE.get(url)
    if cached and (time.monotonic() - cached[0]) < _CACHE_TTL_SECONDS:
        return cached[1]

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        jwks = resp.json()

    _CACHE[url] = (time.monotonic(), jwks)
    return jwks


def find_key(jwks: dict, kid: str) -> dict | None:
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    return None
