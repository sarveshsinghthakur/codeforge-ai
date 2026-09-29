"""Global exception handlers for FastAPI."""
from fastapi import Request
from fastapi.responses import JSONResponse
import structlog

from app.core.exceptions import AppException

logger = structlog.get_logger("codeforge")


async def app_exception_handler(request: Request, exc: AppException):
    logger.warning("App exception", code=exc.code, message=exc.message, status=exc.status_code, path=str(request.url))
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        },
    )


async def validation_exception_handler(request: Request, exc):
    logger.warning("Validation error", errors=exc.errors(), path=str(request.url))
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": exc.errors()},
            },
        },
    )


async def http_exception_handler(request: Request, exc):
    logger.warning("HTTP exception", status=exc.status_code, detail=exc.detail, path=str(request.url))
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
            },
        },
    )
