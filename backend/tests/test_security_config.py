"""Production-safety config checks: refuse to boot with insecure dev defaults."""
import pytest

from app.core.config import DEV_JWT_SECRET, Settings


def _settings(**overrides) -> Settings:
    base = dict(environment="production", jwt_secret="x" * 40, cors_allow_origins=["https://app.example.com"])
    base.update(overrides)
    return Settings(**base)


def test_development_skips_safety_checks():
    # The dev default secret + wildcard CORS are fine outside production.
    s = Settings(environment="development", jwt_secret=DEV_JWT_SECRET, cors_allow_origins=["*"])
    s.validate_production_safety()  # should not raise


def test_production_rejects_dev_jwt_secret():
    s = _settings(jwt_secret=DEV_JWT_SECRET)
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        s.validate_production_safety()


def test_production_rejects_short_jwt_secret():
    s = _settings(jwt_secret="too-short")
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        s.validate_production_safety()


def test_production_rejects_wildcard_cors():
    s = _settings(cors_allow_origins=["*"])
    with pytest.raises(RuntimeError, match="CORS"):
        s.validate_production_safety()


def test_production_accepts_strong_config():
    _settings().validate_production_safety()  # should not raise
