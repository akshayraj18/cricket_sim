from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# The development fallback for `jwt_secret`. Shipping this in production would let
# anyone forge access tokens, so we refuse to start with it when not in dev
# (see `Settings.validate_production_safety`).
DEV_JWT_SECRET = "dev-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://cricket_sim:cricket_sim@localhost:5432/cricket_sim"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = DEV_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # CORS. A native mobile app sends no browser Origin, so this only matters for
    # web callers. In production set CORS_ALLOW_ORIGINS to an explicit,
    # comma-separated allowlist; the "*" default is for local dev only and is
    # rejected at startup when `environment` is "production".
    cors_allow_origins: Annotated[list[str], NoDecode] = ["*"]

    # Rate limiting (Redis-backed fixed window) for the auth endpoints, to blunt
    # credential/token abuse. True network-layer DDoS is handled upstream (WAF /
    # CDN / reverse proxy); this caps per-client request bursts at the app.
    rate_limit_enabled: bool = True
    auth_rate_limit_per_minute: int = 20

    # Sign in with Apple: https://appleid.apple.com/.well-known/openid-configuration
    # The audience (aud) of an Apple identity token is the app's bundle ID.
    apple_client_ids: list[str] = ["com.akshraj.cric"]
    apple_issuer: str = "https://appleid.apple.com"
    apple_jwks_url: str = "https://appleid.apple.com/auth/keys"

    # Google Sign-In / Google Play Games.
    # The audience (aud) of the idToken is the Web OAuth client ID configured in
    # the mobile app's GoogleSignin.configure({ webClientId }). Set the real ID
    # via the GOOGLE_CLIENT_IDS env var (comma-separated) or .env. The iOS
    # client ID may also appear as the aud, so include both once known.
    google_client_ids: list[str] = [
        "474477947414-jb0fkhakmtdctplqmk9rlno8bguke6al.apps.googleusercontent.com",  # Web client (idToken aud)
        "474477947414-bff512hqin1s695shti2nic0dg1t31hk.apps.googleusercontent.com",  # iOS client (fallback aud)
    ]
    google_issuers: list[str] = ["https://accounts.google.com", "accounts.google.com"]
    google_jwks_url: str = "https://www.googleapis.com/oauth2/v3/certs"

    # Observability. Sentry is disabled unless a DSN is provided (so dev/test
    # don't send events). `environment` tags events; `traces_sample_rate`
    # controls performance-trace sampling (0 = errors only).
    sentry_dsn: str = ""
    environment: str = "development"
    sentry_traces_sample_rate: float = 0.0

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _split_csv(cls, v):
        """Parse CORS_ALLOW_ORIGINS as a plain comma-separated env var
        (e.g. https://a.com,https://b.com) rather than JSON. The field is
        annotated NoDecode so pydantic-settings hands us the raw string."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in ("production", "prod")

    def validate_production_safety(self) -> None:
        """Refuse to run in production with insecure dev defaults. Called at
        app startup so a misconfigured deploy fails fast and loudly rather than
        silently shipping a forgeable JWT secret or wide-open CORS."""
        if not self.is_production:
            return
        problems: list[str] = []
        if self.jwt_secret == DEV_JWT_SECRET or len(self.jwt_secret) < 32:
            problems.append("JWT_SECRET must be set to a strong (>=32 char) value, not the dev default.")
        if "*" in self.cors_allow_origins:
            problems.append("CORS_ALLOW_ORIGINS must be an explicit allowlist, not '*'.")
        if problems:
            raise RuntimeError("Insecure production configuration: " + " ".join(problems))


settings = Settings()
