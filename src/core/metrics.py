from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge

class MetricsManager:
    """Manages Prometheus metrics for bot monitoring."""
    
    def __init__(self):
        self._metrics: Dict[str, Any] = {}
        self._setup_metrics()

    def _setup_metrics(self) -> None:
        """Initialize core metrics."""
        self._metrics = {
            'command_latency': Histogram(
                'bot_command_latency_seconds',
                'Command execution latency',
                ['command']
            ),
            'errors': Counter(
                'bot_errors_total',
                'Number of bot errors',
                ['type']
            ),
            'active_commands': Gauge(
                'bot_active_commands',
                'Number of active commands'
            ),
            'media_streams': Gauge(
                'bot_active_media_streams',
                'Number of active media streams'
            ),
            'queue_size': Gauge(
                'bot_queue_size',
                'Current queue size',
                ['type']
            ),
            'service_health': Gauge(
                'bot_service_health',
                'Service health status',
                ['service']
            )
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get all registered metrics."""
        return self._metrics

    def record_latency(self, command: str, duration: float) -> None:
        """Record command execution latency."""
        self._metrics['command_latency'].labels(command).observe(duration)

    def record_error(self, error_type: str) -> None:
        """Record an error occurrence."""
        self._metrics['errors'].labels(type=error_type).inc()

    def update_gauge(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Update a gauge metric."""
        if name in self._metrics:
            if labels:
                self._metrics[name].labels(**labels).set(value)
            else:
                self._metrics[name].set(value)

    def increment_counter(self, name: str, labels: Dict[str, str] = None) -> None:
        """Increment a counter metric."""
        if name in self._metrics:
            if labels:
                self._metrics[name].labels(**labels).inc()
            else:
                self._metrics[name].inc()