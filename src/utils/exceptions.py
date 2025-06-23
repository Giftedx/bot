"""Custom exceptions for the application."""
from typing import Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ErrorContext:
    """Context information for errors."""

    timestamp: datetime = datetime.now()
    operation: Optional[str] = None
    resource: Optional[str] = None
    details: Optional[dict] = None


class AppError(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        context: Optional[ErrorContext] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.message = message
        self.context = context or ErrorContext()
        self.original_error = original_error


class ConfigError(AppError):
    """Configuration-related errors."""

    pass


class CacheError(AppError):
    """Cache operation errors."""

    pass


class GitHubError(AppError):
    """GitHub API related errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.status_code = status_code


class RateLimitError(GitHubError):
    """Rate limit exceeded errors."""

    def __init__(self, message: str, reset_time: Optional[datetime] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.reset_time = reset_time


class ValidationError(AppError):
    """Data validation errors."""

    def __init__(
        self, message: str, field: Optional[str] = None, value: Optional[Any] = None, **kwargs
    ):
        super().__init__(message, **kwargs)
        self.field = field
        self.value = value


class RepositoryError(AppError):
    """Repository operation errors."""

    pass


class MetricsError(AppError):
    """Metrics collection and reporting errors."""

    pass


def create_error_context(
    operation: Optional[str] = None, resource: Optional[str] = None, **details
) -> ErrorContext:
    """Create an error context with the given information."""
    return ErrorContext(
        timestamp=datetime.now(), operation=operation, resource=resource, details=details or None
    )
