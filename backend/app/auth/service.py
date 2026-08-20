import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    refresh_token_expiry,
)
from app.auth.schemas import AuthResponse, TokenPair, UserOut
from app.db.models.user import RefreshToken, User


def _utc_now() -> datetime:
    """Naive UTC datetime, matching the TIMESTAMP WITHOUT TIME ZONE columns it's stored in."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AuthError(Exception):
    pass


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        has_apple_link=user.apple_sub is not None,
        has_google_link=user.google_sub is not None,
    )


async def issue_token_pair(db: AsyncSession, user: User) -> TokenPair:
    access_token = create_access_token(user.id)

    refresh_token = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=refresh_token_expiry(),
        )
    )

    return TokenPair(access_token=access_token, refresh_token=refresh_token)


async def create_guest_user(db: AsyncSession) -> AuthResponse:
    user = User(last_login_at=_utc_now())
    db.add(user)
    await db.flush()

    tokens = await issue_token_pair(db, user)
    await db.commit()

    return AuthResponse(user=_user_out(user), tokens=tokens)


async def get_user_by_apple_sub(db: AsyncSession, apple_sub: str) -> User | None:
    result = await db.execute(select(User).where(User.apple_sub == apple_sub))
    return result.scalar_one_or_none()


async def get_user_by_google_sub(db: AsyncSession, google_sub: str) -> User | None:
    result = await db.execute(select(User).where(User.google_sub == google_sub))
    return result.scalar_one_or_none()


async def sign_in_with_apple(
    db: AsyncSession, apple_sub: str, email: str | None, display_name: str | None
) -> AuthResponse:
    user = await get_user_by_apple_sub(db, apple_sub)
    if user is None:
        user = User(apple_sub=apple_sub, email=email, display_name=display_name)
        db.add(user)
        await db.flush()

    user.last_login_at = _utc_now()

    tokens = await issue_token_pair(db, user)
    await db.commit()

    return AuthResponse(user=_user_out(user), tokens=tokens)


async def sign_in_with_google(
    db: AsyncSession, google_sub: str, email: str | None, display_name: str | None
) -> AuthResponse:
    user = await get_user_by_google_sub(db, google_sub)
    if user is None:
        user = User(google_sub=google_sub, email=email, display_name=display_name)
        db.add(user)
        await db.flush()

    user.last_login_at = _utc_now()

    tokens = await issue_token_pair(db, user)
    await db.commit()

    return AuthResponse(user=_user_out(user), tokens=tokens)


async def link_apple_account(db: AsyncSession, user: User, apple_sub: str, email: str | None) -> UserOut:
    existing = await get_user_by_apple_sub(db, apple_sub)
    if existing is not None and existing.id != user.id:
        raise AuthError("This Apple account is already linked to another user")

    user.apple_sub = apple_sub
    if email and not user.email:
        user.email = email

    await db.commit()
    return _user_out(user)


async def link_google_account(db: AsyncSession, user: User, google_sub: str, email: str | None) -> UserOut:
    existing = await get_user_by_google_sub(db, google_sub)
    if existing is not None and existing.id != user.id:
        raise AuthError("This Google account is already linked to another user")

    user.google_sub = google_sub
    if email and not user.email:
        user.email = email

    await db.commit()
    return _user_out(user)


async def refresh_session(db: AsyncSession, raw_refresh_token: str) -> TokenPair:
    token_hash = hash_refresh_token(raw_refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    stored = result.scalar_one_or_none()

    if stored is None:
        raise AuthError("Invalid refresh token")

    now = _utc_now()
    if stored.revoked_at is not None or stored.expires_at < now:
        raise AuthError("Refresh token expired or revoked")

    user = await db.get(User, stored.user_id)
    if user is None:
        raise AuthError("Invalid refresh token")

    # Rotate: revoke the used token and issue a new pair.
    stored.revoked_at = now
    tokens = await issue_token_pair(db, user)
    await db.commit()

    return tokens


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await db.get(User, user_id)


async def delete_user(db: AsyncSession, user: User) -> None:
    """Permanently delete a user and everything they own.

    Required by Apple App Store Guideline 5.1.1(v): an app that creates accounts
    must let the user delete theirs in-app. Every table referencing users.id is
    declared ON DELETE CASCADE (refresh_tokens, careers — and careers cascade to
    teams/players/matches/stats — plus subscriptions/entitlements), so removing
    the User row removes all of their data in one transaction. This is
    irreversible.
    """
    await db.delete(user)
    await db.commit()


async def set_player_name_overrides(
    db: AsyncSession, user: User, overrides: dict[str, str]
) -> User:
    """Persist a user's player-name overrides.

    An empty mapping is stored as NULL rather than {} so "no overrides" has one
    representation, and clearing them is just an import with nothing changed.
    """
    user.player_name_overrides = overrides or None
    await db.commit()
    await db.refresh(user)
    return user
