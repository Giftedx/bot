"""Backpressure handling system for managing request load and rate limiting.

This module provides backpressure mechanisms to handle high load scenarios by:
- Throttling incoming requests when system is under heavy load
- Implementing sliding window rate limiting
- Managing request queues with prioritization

Typical usage example:
    from core.backpressure import Backpressure, BackpressureConfig
    config = BackpressureConfig(max_concurrent=10, window_size=60, reject_threshold=0.8)
    bp = Backpressure(config)
    await bp.execute(my_async_func, *args)
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
    """System load metrics.
    
    Attributes:
        request_rate: Current request rate (requests per window)
        queue_size: Size of the request queue
        latency: Average request latency (seconds)
        error_rate: Error rate over the window
    """
    request_rate: float
    queue_size: int
    latency: float
    error_rate: float


@dataclass
class BackpressureConfig:
    """Configuration for backpressure handling.
    
    Attributes:
        max_concurrent: Maximum number of concurrent requests
        window_size: Size of the sliding window for rate limiting
        reject_threshold: Request rate threshold for rejecting new requests
    """
    max_concurrent: int
    window_size: int
    reject_threshold: float


T = TypeVar('T')


class Backpressure:
    """Core backpressure implementation.
    
    Manages concurrent request execution and rate limiting using a sliding window algorithm.
    """

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
            Exception: Propagates exceptions from the executed function
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
        """Update internal load metrics.
        
        Updates request rate and latency based on the sliding window.
        """
        if self._window:
            self._metrics.request_rate = (
                len(self._window) / self._config.window_size
            )
            self._metrics.latency = sum(self._window) / len(self._window)


class LoadManager:
    """Manages system load monitoring.
    
    Provides access to current system load metrics for monitoring and scaling decisions.
    """

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
