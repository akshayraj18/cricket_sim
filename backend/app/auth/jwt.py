import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from jwt import PyJWTError

from app.core.config import settings


class TokenError(Exception):
    pass


def create_access_token(user_id: uuid.UUID) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except PyJWTError as exc:
        raise TokenError("Invalid or expired access token") from exc

    if payload.get("type") != "access":
        raise TokenError("Not an access token")

    try:
        return uuid.UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise TokenError("Invalid token subject") from exc


def generate_refresh_token() -> str:
    """A high-entropy opaque token (not a JWT) — only its hash is stored server-side."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def refresh_token_expiry() -> datetime:
    """Naive UTC datetime, matching the TIMESTAMP WITHOUT TIME ZONE column it's stored in."""
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=settings.refresh_token_expire_days)
