"""Verification of Sign in with Apple identity tokens.

Apple issues a JWT identity token to the client after a successful Face
ID/Touch ID/Apple ID sign-in. The client forwards that token to us; we verify
its signature against Apple's published JWKS and check standard claims
(issuer, audience, expiry). The verified `sub` claim is Apple's stable,
per-user-per-app identifier — used as `users.apple_sub`.
"""
import jwt
from jwt import PyJWK, PyJWTError

from app.auth.jwks import find_key, get_jwks
from app.core.config import settings


class AppleTokenError(Exception):
    pass


class AppleIdentity:
    def __init__(self, sub: str, email: str | None):
        self.sub = sub
        self.email = email


async def verify_apple_identity_token(identity_token: str) -> AppleIdentity:
    try:
        header = jwt.get_unverified_header(identity_token)
    except PyJWTError as exc:
        raise AppleTokenError("Malformed identity token") from exc

    jwks = await get_jwks(settings.apple_jwks_url)
    key = find_key(jwks, header.get("kid", ""))
    if key is None:
        raise AppleTokenError("No matching Apple signing key for token")

    try:
        claims = jwt.decode(
            identity_token,
            PyJWK.from_dict(key).key,
            # Pin the algorithm instead of trusting the token's `alg` header,
            # which otherwise allows "none"/HMAC downgrade forgery. Apple signs
            # identity tokens with RS256.
            algorithms=["RS256"],
            issuer=settings.apple_issuer,
            options={"verify_aud": False},
        )
    except PyJWTError as exc:
        raise AppleTokenError(f"Apple identity token verification failed: {exc}") from exc

    aud = claims.get("aud")
    aud_values = [aud] if isinstance(aud, str) else (aud or [])
    if not any(a in settings.apple_client_ids for a in aud_values):
        raise AppleTokenError("Apple identity token audience not recognized")

    sub = claims.get("sub")
    if not sub:
        raise AppleTokenError("Apple identity token missing 'sub' claim")

    return AppleIdentity(sub=sub, email=claims.get("email"))
