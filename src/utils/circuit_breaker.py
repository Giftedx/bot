"""Circuit breaker pattern implementation for external service resilience."""
import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Awaitable, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker for handling external service failures gracefully.

    Features:
    - Exponential backoff
    - Half-open state testing
    - Failure rate threshold
    - Success threshold for recovery
    - Sliding window for failure counting
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        recovery_timeout: float = 60.0,
        backoff_factor: float = 2.0,
        max_backoff: float = 300.0,
        window_size: int = 10,
    ):
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._failure_threshold = failure_threshold
        self._success_threshold = success_threshold
        self._recovery_timeout = recovery_timeout
        self._backoff_factor = backoff_factor
        self._max_backoff = max_backoff
        self._window_size = window_size
        self._failure_times: list[datetime] = []
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    async def call(self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
        """
        Execute a function with circuit breaker protection.

        Args:
            func: Async function to execute
            args: Positional arguments for func
            kwargs: Keyword arguments for func

        Returns:
            The result of func

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Any exception from func
        """
        async with self._lock:
            if self._state == CircuitState.OPEN:
                if await self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                else:
                    raise CircuitBreakerError(
                        "Circuit breaker is open", retry_after=self._get_retry_after()
                    )

            try:
                result = await func(*args, **kwargs)
                await self._handle_success()
                return result

            except Exception:
                await self._handle_failure()
                raise

    async def _handle_success(self) -> None:
        """Handle successful call."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self._success_threshold:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
                self._failure_times.clear()
                logger.info("Circuit breaker reset to closed state")

    async def _handle_failure(self) -> None:
        """Handle failed call."""
        now = datetime.now()
        self._last_failure_time = now
        self._failure_times.append(now)

        # Maintain sliding window
        window_start = now - timedelta(seconds=self._window_size)
        self._failure_times = [t for t in self._failure_times if t >= window_start]

        self._failure_count = len(self._failure_times)
        if self._failure_count >= self._failure_threshold:
            self._state = CircuitState.OPEN
            self._success_count = 0
            logger.warning(f"Circuit breaker opened after {self._failure_count} failures")

    async def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try resetting."""
        if not self._last_failure_time:
            return True

        elapsed = (datetime.now() - self._last_failure_time).total_seconds()
        timeout = min(
            self._recovery_timeout * (self._backoff_factor**self._failure_count),
            self._max_backoff,
        )
        return elapsed >= timeout

    def _get_retry_after(self) -> float:
        """Calculate time until next retry attempt."""
        if not self._last_failure_time:
            return 0

        elapsed = (datetime.now() - self._last_failure_time).total_seconds()
        timeout = min(
            self._recovery_timeout * (self._backoff_factor**self._failure_count),
            self._max_backoff,
        )
        return max(0, timeout - elapsed)


class CircuitBreakerError(Exception):
    """Raised when circuit breaker prevents an operation."""

    def __init__(self, message: str, retry_after: float):
        super().__init__(message)
        self.retry_after = retry_after
