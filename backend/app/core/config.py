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


settings = Settings()
