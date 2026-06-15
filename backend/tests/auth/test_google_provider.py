"""Unit tests for the real Google ID-token verifier.

The route-level tests in test_auth_routes.py mock `verify_google_id_token`, so
they never exercise the actual JWKS signature check or claim validation. These
tests sign tokens with a throwaway RSA key, stub the JWKS fetch to return the
matching public key, and run the verifier for real.

The headline case is `at_hash`: Google ID tokens carry an `at_hash` claim, and
python-jose verifies it against an OAuth access_token by default. The app only
forwards the ID token (no access_token), so verification must skip `at_hash` —
this is the regression that broke real Google sign-in.
"""
import time
import uuid

import pytest

from app.auth.providers import google
from app.auth.providers.google import GoogleTokenError, verify_google_id_token
from app.core.config import settings

from ._token_signing import at_hash, rsa_keypair, sign, sign_hs256


@pytest.fixture
def google_key(monkeypatch):
    private_key, jwks = rsa_keypair()

    async def fake_get_jwks(url: str) -> dict:
        return jwks

    monkeypatch.setattr(google, "get_jwks", fake_get_jwks)
    return private_key


def _base_claims() -> dict:
    now = int(time.time())
    return {
        "iss": "https://accounts.google.com",
        "aud": settings.google_client_ids[0],
        "sub": f"google-{uuid.uuid4().hex}",
        "email": "player@example.com",
        "iat": now,
        "exp": now + 3600,
    }


async def test_verifies_token_with_at_hash_claim(google_key):
    """The regression: a token carrying at_hash must verify without an access_token."""
    claims = _base_claims()
    claims["at_hash"] = at_hash("some-opaque-access-token")
    token = sign(google_key, claims)

    identity = await verify_google_id_token(token)

    assert identity.sub == claims["sub"]
    assert identity.email == "player@example.com"


async def test_rejects_unknown_audience(google_key):
    claims = _base_claims()
    claims["aud"] = "not-our-client-id.apps.googleusercontent.com"
    token = sign(google_key, claims)

    with pytest.raises(GoogleTokenError):
        await verify_google_id_token(token)


async def test_rejects_unknown_issuer(google_key):
    claims = _base_claims()
    claims["iss"] = "https://evil.example.com"
    token = sign(google_key, claims)

    with pytest.raises(GoogleTokenError):
        await verify_google_id_token(token)


async def test_rejects_expired_token(google_key):
    claims = _base_claims()
    claims["exp"] = int(time.time()) - 10
    token = sign(google_key, claims)

    with pytest.raises(GoogleTokenError):
        await verify_google_id_token(token)


async def test_rejects_token_signed_by_wrong_key(google_key):
    """A token signed by a key that isn't in the published JWKS is rejected."""
    other_key, _ = rsa_keypair()
    token = sign(other_key, _base_claims())

    with pytest.raises(GoogleTokenError):
        await verify_google_id_token(token)


async def test_rejects_hs256_algorithm_confusion(google_key):
    """RS256->HS256 confusion: an HS256-signed token must be rejected because
    the verifier pins accepted algorithms to RS256 (it doesn't trust the
    token's own `alg` header)."""
    token = sign_hs256("public-key-as-hmac-secret", _base_claims())

    with pytest.raises(GoogleTokenError):
        await verify_google_id_token(token)
