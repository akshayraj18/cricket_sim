"""Unit tests for the real Sign in with Apple identity-token verifier.

Like the Google provider tests, these sign tokens with a throwaway RSA key and
stub the JWKS fetch so the real `verify_apple_identity_token` runs against
tokens we control (the route tests mock the verifier and never hit this path).
"""
import time
import uuid

import pytest

from app.auth.providers import apple
from app.auth.providers.apple import AppleTokenError, verify_apple_identity_token
from app.core.config import settings

from ._token_signing import rsa_keypair, sign, sign_hs256


@pytest.fixture
def apple_key(monkeypatch):
    private_key, jwks = rsa_keypair()

    async def fake_get_jwks(url: str) -> dict:
        return jwks

    monkeypatch.setattr(apple, "get_jwks", fake_get_jwks)
    return private_key


def _base_claims() -> dict:
    now = int(time.time())
    return {
        "iss": settings.apple_issuer,
        "aud": settings.apple_client_ids[0],
        "sub": f"apple-{uuid.uuid4().hex}",
        "email": "player@privaterelay.appleid.com",
        "iat": now,
        "exp": now + 3600,
    }


async def test_verifies_valid_token(apple_key):
    claims = _base_claims()
    token = sign(apple_key, claims)

    identity = await verify_apple_identity_token(token)

    assert identity.sub == claims["sub"]
    assert identity.email == "player@privaterelay.appleid.com"


async def test_rejects_hs256_algorithm_confusion(apple_key):
    """RS256->HS256 confusion: an HS256-signed token must be rejected because
    the verifier pins accepted algorithms to RS256 (it doesn't trust the
    token's own `alg` header)."""
    token = sign_hs256("public-key-as-hmac-secret", _base_claims())

    with pytest.raises(AppleTokenError):
        await verify_apple_identity_token(token)


async def test_token_without_email_is_ok(apple_key):
    """Apple only returns email on first sign-in; a later token may omit it."""
    claims = _base_claims()
    del claims["email"]
    token = sign(apple_key, claims)

    identity = await verify_apple_identity_token(token)

    assert identity.sub == claims["sub"]
    assert identity.email is None


async def test_rejects_unknown_audience(apple_key):
    claims = _base_claims()
    claims["aud"] = "com.someone.else"
    token = sign(apple_key, claims)

    with pytest.raises(AppleTokenError):
        await verify_apple_identity_token(token)


async def test_rejects_unknown_issuer(apple_key):
    claims = _base_claims()
    claims["iss"] = "https://evil.example.com"
    token = sign(apple_key, claims)

    with pytest.raises(AppleTokenError):
        await verify_apple_identity_token(token)


async def test_rejects_expired_token(apple_key):
    claims = _base_claims()
    claims["exp"] = int(time.time()) - 10
    token = sign(apple_key, claims)

    with pytest.raises(AppleTokenError):
        await verify_apple_identity_token(token)


async def test_rejects_token_signed_by_wrong_key(apple_key):
    other_key, _ = rsa_keypair()
    token = sign(other_key, _base_claims())

    with pytest.raises(AppleTokenError):
        await verify_apple_identity_token(token)


async def test_rejects_malformed_token(apple_key):
    with pytest.raises(AppleTokenError):
        await verify_apple_identity_token("not-a-jwt")
