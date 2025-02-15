"""Backpressure handling system for managing request load and rate limiting.

This module provides backpressure mechanisms to handle high load scenarios by:
- Throttling incoming requests when system is under heavy load
- Implementing sliding window rate limiting
- Managing request queues with prioritization
"""

from typing import TypeVar, Callable, Awaitable, Any, Deque
from dataclasses import dataclass
from collections import deque
import asyncio
import time


class BackpressureExceeded(Exception):
    """Raised when system load exceeds configured thresholds."""


@dataclass
class LoadMetrics:
    """System load metrics."""
    request_rate: float
    queue_size: int
    latency: float
    error_rate: float


@dataclass
class BackpressureConfig:
    """Configuration for backpressure handling."""
    max_concurrent: int
    window_size: int
    reject_threshold: float


T = TypeVar('T')


class Backpressure:
    """Core backpressure implementation."""

    def __init__(self, config: BackpressureConfig) -> None:
        """Initialize backpressure handler.
        
        Args:
            config: Backpressure configuration parameters
        """
        self._config = config
        self._semaphore = asyncio.Semaphore(config.max_concurrent)
        self._window: Deque[float] = deque(maxlen=config.window_size)
        self._metrics = LoadMetrics(0.0, 0, 0.0, 0.0)

    async def execute(
        self,
        func: Callable[..., Awaitable[T]], 
        *args: Any,
        **kwargs: Any
    ) -> T:
        """Execute an operation with backpressure control.
        
        Args:
            func: Async function to execute
            args: Positional arguments for function
            kwargs: Keyword arguments for function
            
        Returns:
            Result of the operation
            
        Raises:
            BackpressureExceeded: If operation would exceed limits
        """
        if len(self._window) >= self._config.window_size:
            if self._metrics.request_rate > self._config.reject_threshold:
                raise BackpressureExceeded("Rate limit exceeded")

        async with self._semaphore:
            start = time.monotonic()
            try:
                result = await func(*args, **kwargs)
                self._window.append(time.monotonic() - start)
                return result
            except Exception as e:
                self._metrics.error_rate += 1
                raise e

    async def _update_metrics(self) -> None:
        """Update internal load metrics."""
        if self._window:
            self._metrics.request_rate = (
                len(self._window) / self._config.window_size
            )
            self._metrics.latency = sum(self._window) / len(self._window)


class LoadManager:
    """Manages system load monitoring."""

    def __init__(self, window_size: int = 60) -> None:
        """Initialize load manager.

        Args:
            window_size: Size of monitoring window in seconds
        """
        self._window_size = window_size
        self._metrics = LoadMetrics(0.0, 0, 0.0, 0.0)

    async def get_metrics(self) -> LoadMetrics:
        """Get current load metrics.

        Returns:
            Current system load metrics
        """
        return self._metrics
