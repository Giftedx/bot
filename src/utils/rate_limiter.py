"""Rate limiter for API calls."""
from typing import Optional, Dict, Any
from dataclasses import dataclass
import time
import asyncio
from datetime import datetime
from .logger import get_logger
from .metrics import metrics
from .config import config

logger = get_logger(__name__)


@dataclass
class RateLimit:
    """Rate limit information."""

    remaining: int
    reset_time: float
    limit: int


class RateLimiter:
    """Rate limiter with token bucket algorithm."""

    def __init__(self, calls_per_second: float = 1.0, burst_size: int = 30):
        self.rate = calls_per_second
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary."""
        async with self._lock:
            while self.tokens <= 0:
                now = time.time()
                time_passed = now - self.last_update
                new_tokens = time_passed * self.rate

                if new_tokens > 0:
                    self.tokens = min(self.burst_size, self.tokens + new_tokens)
                    self.last_update = now
                else:
                    await asyncio.sleep(1.0 / self.rate)

            self.tokens -= 1


class GitHubRateLimiter:
    """GitHub-specific rate limiter with quota tracking."""

    def __init__(self):
        self.limits: Dict[str, RateLimit] = {}
        self.rate_limiter = RateLimiter(
            calls_per_second=0.8, burst_size=30  # Slightly conservative
        )

    def update_limits(self, category: str, remaining: int, reset_time: float, limit: int) -> None:
        """Update rate limit information for a category."""
        self.limits[category] = RateLimit(remaining, reset_time, limit)

        # Update metrics
        metrics.update_rate_limit(category, remaining, int(reset_time))

        if remaining < (limit * 0.1):  # Less than 10% remaining
            logger.warning(
                f"GitHub API rate limit for {category} is low: "
                f"{remaining}/{limit} remaining, "
                f"resets at {datetime.fromtimestamp(reset_time)}"
            )

    def get_limit(self, category: str) -> Optional[RateLimit]:
        """Get rate limit information for a category."""
        return self.limits.get(category)

    async def check_limit(self, category: str, required: int = 1) -> bool:
        """Check if we have enough quota remaining."""
        limit = self.get_limit(category)
        if not limit:
            return True  # No limit information yet

        if limit.remaining < required:
            wait_time = max(0, limit.reset_time - time.time())
            if wait_time > 0:
                logger.info(
                    f"Rate limit for {category} exceeded, " f"waiting {wait_time:.1f} seconds"
                )
                await asyncio.sleep(wait_time)
            return False

        return True

    async def acquire(self, category: str, required: int = 1) -> bool:
        """Acquire permission to make API calls."""
        # First check GitHub's rate limits
        if not await self.check_limit(category, required):
            return False

        # Then apply our own rate limiting
        try:
            await self.rate_limiter.acquire()
            return True
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            return False


# Global rate limiter instance
github_limiter = GitHubRateLimiter()
