"""Health check system for monitoring service health."""
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
import asyncio
import time
from datetime import datetime, timedelta
from .logger import get_logger
from .metrics import metrics
from .config import config
from .exceptions import AppError

logger = get_logger(__name__)


@dataclass
class HealthCheck:
    """Health check definition."""

    name: str
    check_func: Callable
    interval: float
    timeout: float
    last_check: Optional[datetime] = None
    last_status: bool = False
    consecutive_failures: int = 0
    error_message: Optional[str] = None


class HealthManager:
    """Manages service health checks."""

    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self._stop_event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None

    def add_check(
        self, name: str, check_func: Callable, interval: float = 60.0, timeout: float = 10.0
    ) -> None:
        """Add a health check."""
        self.checks[name] = HealthCheck(
            name=name, check_func=check_func, interval=interval, timeout=timeout
        )
        logger.info(f"Added health check: {name}")

    async def start(self) -> None:
        """Start health checking."""
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_checks())
        logger.info("Health manager started")

    async def stop(self) -> None:
        """Stop health checking."""
        self._stop_event.set()
        if self._task:
            await self._task
            self._task = None
        logger.info("Health manager stopped")

    async def _run_checks(self) -> None:
        """Run health checks periodically."""
        while not self._stop_event.is_set():
            for check in self.checks.values():
                # Check if it's time to run this check
                if not check.last_check or datetime.now() - check.last_check > timedelta(
                    seconds=check.interval
                ):
                    await self._execute_check(check)

            await asyncio.sleep(1.0)  # Check every second

    async def _execute_check(self, check: HealthCheck) -> None:
        """Execute a single health check."""
        check.last_check = datetime.now()

        try:
            # Run check with timeout
            async with metrics.measure_latency("health_check"):
                result = await asyncio.wait_for(check.check_func(), timeout=check.timeout)

            check.last_status = bool(result)
            if check.last_status:
                check.consecutive_failures = 0
                check.error_message = None
            else:
                check.consecutive_failures += 1
                check.error_message = "Check returned False"

        except asyncio.TimeoutError:
            check.last_status = False
            check.consecutive_failures += 1
            check.error_message = f"Check timed out after {check.timeout}s"

        except Exception as e:
            check.last_status = False
            check.consecutive_failures += 1
            check.error_message = str(e)

        # Update metrics
        metrics.update_service_health(check.name, int(check.last_status))

        # Log status changes
        if check.consecutive_failures == 1:  # First failure
            logger.warning(f"Health check {check.name} failed: {check.error_message}")
        elif check.consecutive_failures == 0:  # Recovery
            logger.info(f"Health check {check.name} recovered")

    def get_status(self) -> Dict[str, Any]:
        """Get current health status."""
        status = {"overall_healthy": True, "timestamp": datetime.now().isoformat(), "checks": {}}

        for name, check in self.checks.items():
            check_status = {
                "healthy": check.last_status,
                "last_check": check.last_check.isoformat() if check.last_check else None,
                "consecutive_failures": check.consecutive_failures,
                "error": check.error_message,
            }
            status["checks"][name] = check_status

            if not check.last_status:
                status["overall_healthy"] = False

        return status

    def is_healthy(self) -> bool:
        """Check if all services are healthy."""
        return all(check.last_status for check in self.checks.values())


# Common health checks
async def check_github_api():
    """Check GitHub API health."""
    from .rate_limiter import github_limiter

    try:
        # Try to get rate limit info
        limit = github_limiter.get_limit("core")
        return limit and limit.remaining > 0
    except Exception as e:
        logger.error(f"GitHub API health check failed: {e}")
        return False


async def check_cache():
    """Check cache health."""
    from .cache import cache

    try:
        test_key = "_health_check"
        test_value = datetime.now().isoformat()

        # Try to write and read from cache
        cache.set(test_key, test_value, ttl=60)
        result = cache.get(test_key)
        cache.delete(test_key)

        return result == test_value
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return False


async def check_metrics():
    """Check metrics system health."""
    try:
        # Try to update a metric
        metrics.update_service_health("health_check", 1)
        return True
    except Exception as e:
        logger.error(f"Metrics health check failed: {e}")
        return False


# Global health manager instance
health_manager = HealthManager()

# Add default health checks
health_manager.add_check("github_api", check_github_api)
health_manager.add_check("cache", check_cache)
health_manager.add_check("metrics", check_metrics)
