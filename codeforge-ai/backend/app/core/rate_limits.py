"""Rate limiting configuration."""
from app.core.config import settings


RATE_LIMITS = {
    "login": settings.rate_limit_login,
    "register": settings.rate_limit_register,
    "submission": settings.rate_limit_submission,
    "ai": settings.rate_limit_ai,
    "generate": settings.rate_limit_generate,
}
