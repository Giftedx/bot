"""Centralized error management system for the Discord bot.

This module provides a unified approach to error handling, logging, and recovery
across all bot components.
"""

import logging
import traceback
import asyncio
from typing import Dict, List, Any, Optional, Callable, Type
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager
from functools import wraps

import discord
from discord.ext import commands
from prometheus_client import Counter, Histogram


logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""

    DATABASE = "database"
    DISCORD_API = "discord_api"
    EXTERNAL_API = "external_api"
    VALIDATION = "validation"
    PERMISSION = "permission"
    RATE_LIMIT = "rate_limit"
    NETWORK = "network"
    SYSTEM = "system"
    USER_INPUT = "user_input"
    UNKNOWN = "unknown"


@dataclass
class ErrorPolicy:
    """Configuration for error handling behavior."""

    max_retries: int = 3
    retry_delay: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay: float = 60.0
    should_notify: bool = False
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    category: ErrorCategory = ErrorCategory.UNKNOWN
    custom_message: Optional[str] = None


@dataclass
class ErrorRecord:
    """Record of an error occurrence."""

    timestamp: datetime = field(default_factory=datetime.now)
    error_type: str = ""
    message: str = ""
    traceback: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    category: ErrorCategory = ErrorCategory.UNKNOWN
    retry_count: int = 0
    resolved: bool = False


class ErrorManager:
    """Central error management system."""

    def __init__(self, bot: Optional[commands.Bot] = None):
        """Initialize error manager."""
        self.bot = bot
        self.error_records: List[ErrorRecord] = []
        self.error_counts: Dict[str, int] = {}
        self.error_policies: Dict[Type[Exception], ErrorPolicy] = {}
        self.notification_handlers: List[Callable] = []

        # Metrics
        self.error_counter = Counter(
            "bot_errors_total", "Total number of errors", ["error_type", "severity", "category"]
        )

        self.error_duration = Histogram(
            "bot_error_duration_seconds", "Time spent handling errors", ["error_type"]
        )

        # Default error policies
        self._setup_default_policies()

    def _setup_default_policies(self) -> None:
        """Set up default error handling policies."""

        # Discord API errors
        self.register_policy(
            discord.HTTPException,
            ErrorPolicy(
                max_retries=2,
                retry_delay=1.0,
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.DISCORD_API,
                custom_message="Discord API temporarily unavailable. Please try again.",
            ),
        )

        self.register_policy(
            discord.RateLimited,
            ErrorPolicy(
                max_retries=1,
                retry_delay=2.0,
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.RATE_LIMIT,
                custom_message="Rate limited. Please wait before trying again.",
            ),
        )

        self.register_policy(
            discord.Forbidden,
            ErrorPolicy(
                max_retries=0,
                severity=ErrorSeverity.LOW,
                category=ErrorCategory.PERMISSION,
                custom_message="I don't have permission to do that.",
            ),
        )

        # Command errors
        self.register_policy(
            commands.CommandNotFound,
            ErrorPolicy(
                max_retries=0,
                severity=ErrorSeverity.LOW,
                category=ErrorCategory.USER_INPUT,
                custom_message=None,  # Don't show error for unknown commands
            ),
        )

        self.register_policy(
            commands.MissingRequiredArgument,
            ErrorPolicy(
                max_retries=0,
                severity=ErrorSeverity.LOW,
                category=ErrorCategory.USER_INPUT,
                custom_message="Missing required argument. Check command usage.",
            ),
        )

        self.register_policy(
            commands.BadArgument,
            ErrorPolicy(
                max_retries=0,
                severity=ErrorSeverity.LOW,
                category=ErrorCategory.USER_INPUT,
                custom_message="Invalid argument provided. Check command usage.",
            ),
        )

        # Database errors
        self.register_policy(
            Exception,  # Generic fallback
            ErrorPolicy(
                max_retries=1,
                retry_delay=0.5,
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.SYSTEM,
                should_notify=True,
                custom_message="An unexpected error occurred. This has been logged.",
            ),
        )

    def register_policy(self, exception_type: Type[Exception], policy: ErrorPolicy) -> None:
        """Register an error handling policy for an exception type."""
        self.error_policies[exception_type] = policy
        logger.debug(f"Registered error policy for {exception_type.__name__}")

    def add_notification_handler(self, handler: Callable) -> None:
        """Add a notification handler for critical errors."""
        self.notification_handlers.append(handler)

    def get_policy(self, exception: Exception) -> ErrorPolicy:
        """Get the error policy for an exception."""
        exception_type = type(exception)

        # Look for exact match first
        if exception_type in self.error_policies:
            return self.error_policies[exception_type]

        # Look for parent class matches
        for registered_type, policy in self.error_policies.items():
            if issubclass(exception_type, registered_type):
                return policy

        # Return default policy
        return self.error_policies.get(Exception, ErrorPolicy())

    async def handle_error(
        self, error: Exception, context: Optional[Dict[str, Any]] = None, retry_count: int = 0
    ) -> Optional[Any]:
        """Handle an error with appropriate policy."""

        start_time = datetime.now()
        policy = self.get_policy(error)

        # Create error record
        error_record = ErrorRecord(
            error_type=type(error).__name__,
            message=str(error),
            traceback=traceback.format_exc(),
            context=context or {},
            severity=policy.severity,
            category=policy.category,
            retry_count=retry_count,
        )

        # Log error
        self._log_error(error_record)

        # Update metrics
        self.error_counter.labels(
            error_type=error_record.error_type,
            severity=policy.severity.value,
            category=policy.category.value,
        ).inc()

        # Store record
        self.error_records.append(error_record)
        self.error_counts[error_record.error_type] = (
            self.error_counts.get(error_record.error_type, 0) + 1
        )

        # Check if we should notify
        if policy.should_notify or policy.severity == ErrorSeverity.CRITICAL:
            await self._notify_error(error_record)

        # Record duration
        duration = (datetime.now() - start_time).total_seconds()
        self.error_duration.labels(error_type=error_record.error_type).observe(duration)

        return policy.custom_message

    def _log_error(self, record: ErrorRecord) -> None:
        """Log an error record."""
        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
        }.get(record.severity, logging.ERROR)

        logger.log(
            log_level,
            f"Error handled - Type: {record.error_type}, "
            f"Message: {record.message}, "
            f"Category: {record.category.value}, "
            f"Severity: {record.severity.value}",
            extra={"error_record": record, "context": record.context},
        )

    async def _notify_error(self, record: ErrorRecord) -> None:
        """Notify about a critical error."""
        for handler in self.notification_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(record)
                else:
                    handler(record)
            except Exception as e:
                logger.error(f"Notification handler failed: {e}")

    @asynccontextmanager
    async def error_context(self, context: Dict[str, Any], max_retries: Optional[int] = None):
        """Context manager for handling errors with retry logic."""
        retries = 0
        max_attempts = max_retries or 3

        while retries <= max_attempts:
            try:
                yield
                break
            except Exception as e:
                policy = self.get_policy(e)
                effective_max_retries = (
                    max_retries if max_retries is not None else policy.max_retries
                )

                if retries >= effective_max_retries:
                    await self.handle_error(e, context, retries)
                    raise

                # Calculate delay
                delay = min(
                    policy.retry_delay * (policy.backoff_multiplier**retries), policy.max_delay
                )

                logger.warning(
                    f"Retrying after error (attempt {retries + 1}/{effective_max_retries + 1}): {e}"
                )

                if delay > 0:
                    await asyncio.sleep(delay)

                retries += 1

    @staticmethod
    def retry_on_error(max_retries: Optional[int] = None, exceptions: Optional[tuple] = None):
        """Decorator for retrying functions on error.

        Implemented as a staticmethod so it can be used as
        `@ErrorManager.retry_on_error(...)` without an instance.
        """

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                retries = 0
                effective_max_retries = max_retries or 3
                target_exceptions = exceptions or (Exception,)

                while retries <= effective_max_retries:
                    try:
                        if asyncio.iscoroutinefunction(func):
                            return await func(*args, **kwargs)
                        else:
                            return func(*args, **kwargs)
                    except target_exceptions as e:
                        if retries >= effective_max_retries:
                            # Best-effort logging without instance
                            logger.error(
                                "Max retries reached for %s: %s", func.__name__, e, exc_info=True
                            )
                            raise

                        # Use a simple exponential backoff
                        delay = min(1.0 * (2.0 ** retries), 60.0)
                        logger.warning(
                            "Retrying %s after error (attempt %s/%s): %s",
                            func.__name__,
                            retries + 1,
                            effective_max_retries + 1,
                            e,
                        )

                        if delay > 0:
                            await asyncio.sleep(delay)

                        retries += 1

            return wrapper

        return decorator

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        total_errors = len(self.error_records)
        recent_errors = [
            r for r in self.error_records if (datetime.now() - r.timestamp).total_seconds() < 3600
        ]

        severity_counts = {}
        category_counts = {}

        for record in self.error_records:
            severity_counts[record.severity.value] = (
                severity_counts.get(record.severity.value, 0) + 1
            )
            category_counts[record.category.value] = (
                category_counts.get(record.category.value, 0) + 1
            )

        return {
            "total_errors": total_errors,
            "recent_errors_1h": len(recent_errors),
            "error_counts_by_type": dict(self.error_counts),
            "error_counts_by_severity": severity_counts,
            "error_counts_by_category": category_counts,
            "most_common_errors": sorted(
                self.error_counts.items(), key=lambda x: x[1], reverse=True
            )[:10],
        }

    def clear_old_records(self, max_age_hours: int = 24) -> int:
        """Clear old error records."""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        old_count = len(self.error_records)

        self.error_records = [r for r in self.error_records if r.timestamp > cutoff]

        cleared = old_count - len(self.error_records)
        if cleared > 0:
            logger.info(f"Cleared {cleared} old error records")

        return cleared


# Global error manager instance
error_manager = ErrorManager()


def setup_error_handling(bot: commands.Bot) -> ErrorManager:
    """Set up error handling for a bot."""
    error_manager.bot = bot

    # Add bot owner notification handler
    async def notify_owner(record: ErrorRecord):
        if bot.owner_id and record.severity in (ErrorSeverity.HIGH, ErrorSeverity.CRITICAL):
            try:
                owner = await bot.fetch_user(bot.owner_id)
                message = (
                    f"🚨 **{record.severity.value.upper()} ERROR**\n"
                    f"**Type:** {record.error_type}\n"
                    f"**Message:** {record.message}\n"
                    f"**Category:** {record.category.value}\n"
                    f"**Time:** {record.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
                )

                if record.context:
                    context_str = "\n".join(f"**{k}:** {v}" for k, v in record.context.items())
                    message += f"\n**Context:**\n{context_str}"

                # Truncate if too long
                if len(message) > 1900:
                    message = message[:1900] + "..."

                await owner.send(message)
            except Exception as e:
                logger.error(f"Failed to notify owner: {e}")

    error_manager.add_notification_handler(notify_owner)
    return error_manager
