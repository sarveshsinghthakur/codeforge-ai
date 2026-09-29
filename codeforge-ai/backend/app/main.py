"""CodeForge AI - FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.api import (
    auth_router,
    users_router,
    problems_router,
    submissions_router,
    test_cases_router,
    ai_router,
    ai_copilot_router,
    discussions_router,
    contests_router,
    admin_router,
    analytics_router,
    dashboard_router,
)

# Import all models so Base.metadata knows about them
from app.models import user, problem, submission, test_case, user_progress, discussion, contest, ai, favorite  # noqa: F401

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    debug=settings.debug,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

# Include all API routers
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(problems_router, prefix="/api")
app.include_router(submissions_router, prefix="/api")
app.include_router(test_cases_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(ai_copilot_router, prefix="/api")
app.include_router(discussions_router, prefix="/api")
app.include_router(contests_router, prefix="/api")
app.include_router(admin_router, prefix="/api/admin")
app.include_router(analytics_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
