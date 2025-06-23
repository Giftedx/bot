"""Metrics collection and monitoring."""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry, start_http_server

logger = logging.getLogger(__name__)


@dataclass
class MetricsRegistry:
    """Registry for Prometheus metrics."""

    registry: CollectorRegistry = field(default_factory=CollectorRegistry)
    _metrics: Dict[str, Any] = field(default_factory=dict)

    def counter(self, name: str, description: str, labels: Optional[List[str]] = None) -> Counter:
        """Create or get a counter metric."""
        if name not in self._metrics:
            self._metrics[name] = Counter(name, description, labels or [], registry=self.registry)
        return self._metrics[name]

    def gauge(self, name: str, description: str, labels: Optional[List[str]] = None) -> Gauge:
        """Create or get a gauge metric."""
        if name not in self._metrics:
            self._metrics[name] = Gauge(name, description, labels or [], registry=self.registry)
        return self._metrics[name]

    def histogram(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None,
    ) -> Histogram:
        """Create or get a histogram metric."""
        if name not in self._metrics:
            self._metrics[name] = Histogram(
                name,
                description,
                labels or [],
                buckets=buckets or Histogram.DEFAULT_BUCKETS,
                registry=self.registry,
            )
        return self._metrics[name]

    def get(self, name: str) -> Optional[Any]:
        """Get a metric by name."""
        return self._metrics.get(name)

    def clear(self) -> None:
        """Clear all metrics."""
        self._metrics.clear()
        self.registry = CollectorRegistry()


def setup_metrics(port: int = 9090) -> MetricsRegistry:
    """Set up metrics collection."""
    try:
        registry = MetricsRegistry()

        # Bot metrics
        registry.gauge("bot_uptime_seconds", "Bot uptime in seconds")
        registry.gauge("bot_latency_seconds", "Bot latency in seconds")
        registry.gauge("bot_guilds", "Number of guilds the bot is in")
        registry.gauge("bot_users", "Number of users the bot can see")
        registry.counter("bot_commands_total", "Total number of commands executed", ["command"])
        registry.counter("bot_errors_total", "Total number of errors", ["type"])
        registry.histogram(
            "bot_command_latency_seconds",
            "Command execution time",
            ["command"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0],
        )

        # Plex metrics
        registry.gauge("plex_active_streams", "Number of active Plex streams")
        registry.counter("plex_stream_total", "Total number of streams", ["media_type"])
        registry.counter("plex_errors_total", "Total number of Plex errors", ["type"])
        registry.histogram(
            "plex_stream_duration_seconds", "Stream duration in seconds", ["media_type"]
        )

        # Start metrics server
        start_http_server(port, registry=registry.registry)
        logger.info(f"Metrics server started on port {port}")

        return registry

    except Exception as e:
        logger.error(f"Failed to set up metrics: {e}")
        # Return empty registry if setup fails
        return MetricsRegistry()
