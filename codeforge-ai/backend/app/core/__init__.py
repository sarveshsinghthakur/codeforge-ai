"""Global exception handlers for FastAPI."""
from fastapi import Request
from fastapi.responses import JSONResponse
import structlog

from app.core.exceptions import AppException
from app.core.config import settings

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


async def unhandled_exception_handler(request: Request, exc: Exception):
    """Last-resort handler: always answer JSON so clients can show a real message
    instead of a plain-text 500 body (which frontend fetches cannot parse)."""
    try:
        logger.error(
            "Unhandled exception",
            error_type=type(exc).__name__,
            error=str(exc)[:500],
            path=str(request.url),
        )
    except Exception:
        pass  # logging must never break the 500 response
    headers = {}
    origin = request.headers.get("origin")
    if origin and origin in settings.cors_origins_list:
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }
    message = "Something went wrong on the server. Please try again."
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "internal_error",
            "message": message,
            "detail": message,
            "retryable": True,
        },
        headers=headers,
    )
