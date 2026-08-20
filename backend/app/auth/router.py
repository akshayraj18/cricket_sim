from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service
from app.auth.dependencies import get_current_user
from app.core.rate_limit import rate_limit
from app.auth.providers.apple import AppleTokenError, verify_apple_identity_token
from app.auth.providers.google import GoogleTokenError, verify_google_id_token
from app.auth.schemas import (
    AppleSignInRequest,
    AuthResponse,
    GoogleSignInRequest,
    RefreshRequest,
    TokenPair,
    PlayerNamesImportRequest,
    UserOut,
)
from app.db.models.user import User
from app.db.session import get_db
from cricket_sim_engine.sim.player_names import (
    NameImportError,
    export_names_csv,
    parse_names_csv,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        has_apple_link=user.apple_sub is not None,
        has_google_link=user.google_sub is not None,
    )


@router.post("/guest", response_model=AuthResponse, dependencies=[Depends(rate_limit("auth"))])
async def auth_guest(db: AsyncSession = Depends(get_db)) -> AuthResponse:
    """Create a brand-new anonymous account with full immediate access."""
    return await service.create_guest_user(db)


@router.post("/apple", response_model=AuthResponse, dependencies=[Depends(rate_limit("auth"))])
async def auth_apple(body: AppleSignInRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    try:
        identity = await verify_apple_identity_token(body.identity_token)
    except AppleTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    return await service.sign_in_with_apple(db, identity.sub, identity.email, body.display_name)


@router.post("/google", response_model=AuthResponse, dependencies=[Depends(rate_limit("auth"))])
async def auth_google(body: GoogleSignInRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    try:
        identity = await verify_google_id_token(body.id_token)
    except GoogleTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    return await service.sign_in_with_google(db, identity.sub, identity.email, body.display_name)


@router.post("/link/apple", response_model=UserOut)
async def link_apple(
    body: AppleSignInRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    try:
        identity = await verify_apple_identity_token(body.identity_token)
    except AppleTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    try:
        return await service.link_apple_account(db, user, identity.sub, identity.email)
    except service.AuthError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.post("/link/google", response_model=UserOut)
async def link_google(
    body: GoogleSignInRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    try:
        identity = await verify_google_id_token(body.id_token)
    except GoogleTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    try:
        return await service.link_google_account(db, user, identity.sub, identity.email)
    except service.AuthError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.post("/refresh", response_model=TokenPair, dependencies=[Depends(rate_limit("auth"))])
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    try:
        return await service.refresh_session(db, body.refresh_token)
    except service.AuthError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return _user_out(user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Permanently delete the authenticated user and all their data (careers,
    match history, tokens). Required for App Store compliance; irreversible."""
    await service.delete_user(db, user)


@router.get("/me/player-names.csv")
async def export_player_names(user: User = Depends(get_current_user)) -> Response:
    """Every player name in the game, with any override the user has saved.

    Pre-filling saved overrides means an export always reflects the user's
    current setup and can be re-imported unchanged.
    """
    csv_text = export_names_csv(user.player_name_overrides or {})
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="player-names.csv"'},
    )


@router.post("/me/player-names.csv", response_model=dict)
async def import_player_names(
    body: PlayerNamesImportRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Save player-name overrides, applied to careers created from now on.

    Deliberately does NOT touch existing careers: their names are already baked
    into saved lineups, leadership and archived scorecards, and rewriting those
    safely is a per-career operation (LeagueState.rename_player), not a
    settings toggle. The response says how many careers were left alone so the
    client can tell the user rather than leaving them to wonder.
    """
    try:
        overrides = parse_names_csv(body.csv)
    except NameImportError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={"message": "Player names rejected.", "errors": exc.errors},
        ) from exc

    await service.set_player_name_overrides(db, user, overrides)
    return {"renamed": len(overrides)}
