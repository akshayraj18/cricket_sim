"""Verification of Google Sign-In ID tokens.

Mirrors the Apple flow: the client (Android app, via Google Play Games
Services / Google Sign-In) obtains an ID token and forwards it to us. We
verify its signature against Google's published JWKS and check standard
claims. The verified `sub` claim is Google's stable per-user identifier —
used as `users.google_sub`.
"""
from jose import jwt
from jose.exceptions import JWTError

from app.auth.jwks import find_key, get_jwks
from app.core.config import settings


class GoogleTokenError(Exception):
    pass


class GoogleIdentity:
    def __init__(self, sub: str, email: str | None):
        self.sub = sub
        self.email = email


async def verify_google_id_token(id_token: str) -> GoogleIdentity:
    try:
        header = jwt.get_unverified_header(id_token)
    except JWTError as exc:
        raise GoogleTokenError("Malformed identity token") from exc

    jwks = await get_jwks(settings.google_jwks_url)
    key = find_key(jwks, header.get("kid", ""))
    if key is None:
        raise GoogleTokenError("No matching Google signing key for token")

    try:
        claims = jwt.decode(
            id_token,
            key,
            algorithms=[header.get("alg", "RS256")],
            # We verify aud/iss ourselves below. `at_hash` binds the ID token to
            # an OAuth access_token we don't receive (the app sends only the ID
            # token), so skip it — the RS256 signature already guarantees the
            # token's integrity.
            options={"verify_aud": False, "verify_at_hash": False},
        )
    except JWTError as exc:
        raise GoogleTokenError(f"Google identity token verification failed: {exc}") from exc

    if claims.get("iss") not in settings.google_issuers:
        raise GoogleTokenError("Google identity token issuer not recognized")

    aud = claims.get("aud")
    aud_values = [aud] if isinstance(aud, str) else (aud or [])
    if not any(a in settings.google_client_ids for a in aud_values):
        raise GoogleTokenError("Google identity token audience not recognized")

    sub = claims.get("sub")
    if not sub:
        raise GoogleTokenError("Google identity token missing 'sub' claim")

    return GoogleIdentity(sub=sub, email=claims.get("email"))
