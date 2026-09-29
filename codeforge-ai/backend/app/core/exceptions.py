"""Backend exceptions."""
from fastapi import HTTPException


class AppException(HTTPException):
    def __init__(self, status_code: int, code: str, message: str, details: dict = None):
        super().__init__(status_code=status_code, detail={"code": code, "message": message, "details": details or {}})
        self.code = code
        self.message = message
        self.details = details or {}


class ProblemNotFound(AppException):
    def __init__(self):
        super().__init__(404, "PROBLEM_NOT_FOUND", "Problem not found")


class UserNotFound(AppException):
    def __init__(self):
        super().__init__(404, "USER_NOT_FOUND", "User not found")


class SubmissionNotFound(AppException):
    def __init__(self):
        super().__init__(404, "SUBMISSION_NOT_FOUND", "Submission not found")


class DiscussionNotFound(AppException):
    def __init__(self):
        super().__init__(404, "DISCUSSION_NOT_FOUND", "Discussion not found")


class NotFound(AppException):
    def __init__(self, resource: str):
        super().__init__(404, "NOT_FOUND", f"{resource} not found")


class Unauthorized(AppException):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(401, "UNAUTHORIZED", message)


class Forbidden(AppException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(403, "FORBIDDEN", message)


class Conflict(AppException):
    def __init__(self, message: str):
        super().__init__(409, "CONFLICT", message)


class ValidationError(AppException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(422, "VALIDATION_ERROR", message, details)
