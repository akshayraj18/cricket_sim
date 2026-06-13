"""Optional Sentry crash/error reporting for the API.

No-op unless `SENTRY_DSN` is set, so local dev and tests never send events.
When enabled, unhandled exceptions (including those surfaced by the catch-all
handler in `app.core.middleware`) are captured with request context.
"""
import logging
import sys

from app.core.config import settings

logger = logging.getLogger("app.observability")


def init_sentry() -> bool:
    """Initialise Sentry if a DSN is configured. Returns True if enabled.

    Never initialises under pytest (even if a DSN is set in the dev .env), so
    test runs don't ship synthetic errors to the real Sentry project.
    """
    if not settings.sentry_dsn or "pytest" in sys.modules:
        return False

    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        # Don't attach request bodies / headers that may contain tokens.
        send_default_pii=False,
        integrations=[StarletteIntegration(), FastApiIntegration()],
    )
    logger.info("sentry initialised", extra={"environment": settings.environment})
    return True
