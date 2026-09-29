"""API routes package."""
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.problems import router as problems_router
from app.api.submissions import router as submissions_router
from app.api.test_cases import router as test_cases_router
from app.api.ai import router as ai_router
from app.api.ai_copilot import router as ai_copilot_router
from app.api.discussions import router as discussions_router
from app.api.contests import router as contests_router
from app.api.admin import router as admin_router
from app.api.analytics import router as analytics_router
from app.api.dashboard import router as dashboard_router

__all__ = [
    "auth_router",
    "users_router",
    "problems_router",
    "submissions_router",
    "test_cases_router",
    "ai_router",
    "ai_copilot_router",
    "discussions_router",
    "contests_router",
    "admin_router",
    "analytics_router",
    "dashboard_router",
]
