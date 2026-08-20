import uuid

from pydantic import BaseModel


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: uuid.UUID
    email: str | None
    display_name: str | None
    has_apple_link: bool
    has_google_link: bool


class AuthResponse(BaseModel):
    user: UserOut
    tokens: TokenPair


class AppleSignInRequest(BaseModel):
    identity_token: str
    display_name: str | None = None


class GoogleSignInRequest(BaseModel):
    id_token: str
    display_name: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class PlayerNamesImportRequest(BaseModel):
    """An edited player-names CSV (player_key,name), sent as text."""

    csv: str
