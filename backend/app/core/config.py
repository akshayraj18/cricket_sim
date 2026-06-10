from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://cricket_sim:cricket_sim@localhost:5432/cricket_sim"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # Sign in with Apple: https://appleid.apple.com/.well-known/openid-configuration
    apple_client_ids: list[str] = ["com.example.cricketsim"]
    apple_issuer: str = "https://appleid.apple.com"
    apple_jwks_url: str = "https://appleid.apple.com/auth/keys"

    # Google Sign-In / Google Play Games
    google_client_ids: list[str] = ["YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"]
    google_issuers: list[str] = ["https://accounts.google.com", "accounts.google.com"]
    google_jwks_url: str = "https://www.googleapis.com/oauth2/v3/certs"


settings = Settings()
