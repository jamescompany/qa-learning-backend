from typing import Any, Optional, Dict
from fastapi import HTTPException, status


class BaseAPIException(HTTPException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Internal server error"
    headers = None

    def __init__(
        self,
        detail: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=self.status_code,
            detail=detail or self.detail,
            headers=headers or self.headers,
        )


class BadRequestException(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Bad request"


class UnauthorizedException(BaseAPIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Unauthorized"
    headers = {"WWW-Authenticate": "Bearer"}


class ForbiddenException(BaseAPIException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Forbidden"


class NotFoundException(BaseAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found"


class ConflictException(BaseAPIException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Conflict"


class ValidationException(BaseAPIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "Validation error"


class RateLimitException(BaseAPIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    detail = "Too many requests"


class UserNotFoundException(NotFoundException):
    detail = "User not found"


class PostNotFoundException(NotFoundException):
    detail = "Post not found"


class TodoNotFoundException(NotFoundException):
    detail = "Todo not found"


class CommentNotFoundException(NotFoundException):
    detail = "Comment not found"


class FileNotFoundException(NotFoundException):
    detail = "File not found"


class InvalidCredentialsException(UnauthorizedException):
    detail = "Invalid email or password"


class TokenExpiredException(UnauthorizedException):
    detail = "Token has expired"


class InvalidTokenException(UnauthorizedException):
    detail = "Invalid token"


class EmailAlreadyExistsException(ConflictException):
    detail = "Email already registered"


class UsernameAlreadyExistsException(ConflictException):
    detail = "Username already taken"


class InsufficientPermissionsException(ForbiddenException):
    detail = "Insufficient permissions to perform this action"


class FileSizeException(BadRequestException):
    detail = "File size exceeds maximum allowed size"


class FileTypeException(BadRequestException):
    detail = "File type not allowed"


class DatabaseException(BaseAPIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Database error occurred"


class ExternalServiceException(BaseAPIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    detail = "External service unavailable"