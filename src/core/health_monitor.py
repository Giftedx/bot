import logging
import asyncio
from typing import Dict, Callable, Any, Optional
from datetime import datetime, timedelta
from prometheus_client import Counter, Gauge

logger = logging.getLogger(__name__)

class HealthMonitor:
    """Manages health checks for various bot services"""
    
    def __init__(self, check_interval: float = 60.0):
        self._checks: Dict[str, Callable[[], Any]] = {}
        self._check_interval = check_interval
        self._last_check_times: Dict[str, datetime] = {}
        self._shutdown_event = asyncio.Event()
        
        # Health metrics
        self._health_gauge = Gauge(
            'service_health_status',
            'Service health status (1=healthy, 0=unhealthy)',
            ['service']
        )
        self._check_errors = Counter(
            'health_check_errors_total',
            'Number of health check errors',
            ['service']
        )

    def register_check(self, name: str, check_func: Callable[[], Any]) -> None:
        """Register a new health check"""
        self._checks[name] = check_func
        self._health_gauge.labels(service=name).set(1)  # Initialize as healthy

    async def start(self) -> None:
        """Start health monitoring"""
        while not self._shutdown_event.is_set():
            await self.run_checks()
            await asyncio.sleep(self._check_interval)

    async def run_checks(self) -> Dict[str, bool]:
        """Run all registered health checks"""
        results = {}
        
        for name, check in self._checks.items():
            try:
                # Skip if check was run recently
                if self._was_checked_recently(name):
                    continue
                    
                result = await check() if asyncio.iscoroutinefunction(check) else check()
                results[name] = bool(result)
                self._update_metrics(name, results[name])
                self._last_check_times[name] = datetime.now()
                
            except Exception as e:
                logger.error(f"Health check '{name}' failed: {e}")
                results[name] = False
                self._update_metrics(name, False)
                self._check_errors.labels(service=name).inc()
                
        return results

    def _was_checked_recently(self, name: str, min_interval: float = 5.0) -> bool:
        """Check if service was checked recently to prevent hammering"""
        last_check = self._last_check_times.get(name)
        if not last_check:
            return False
            
        return (datetime.now() - last_check) < timedelta(seconds=min_interval)

    def _update_metrics(self, name: str, is_healthy: bool) -> None:
        """Update Prometheus metrics for service health"""
        self._health_gauge.labels(service=name).set(1 if is_healthy else 0)

    def get_status(self) -> Dict[str, bool]:
        """Get current health status of all services"""
        return {
            name: self._health_gauge.labels(service=name)._value.get() == 1
            for name in self._checks.keys()
        }

    async def shutdown(self) -> None:
        """Gracefully shutdown health monitoring"""
        self._shutdown_event.set()