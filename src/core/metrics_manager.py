from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge
from dataclasses import dataclass, field

@dataclass
class BotMetrics:
    """Container for bot-related Prometheus metrics"""
    command_latency: Histogram = field(default_factory=lambda: Histogram(
        'bot_command_latency_seconds',
        'Command execution latency',
        ['command']
    ))
    errors: Counter = field(default_factory=lambda: Counter(
        'bot_errors_total',
        'Number of bot errors',
        ['type']
    ))
    active_commands: Gauge = field(default_factory=lambda: Gauge(
        'bot_active_commands',
        'Number of active commands'
    ))
    active_streams: Gauge = field(default_factory=lambda: Gauge(
        'bot_active_streams',
        'Number of active media streams'
    ))
    queue_size: Gauge = field(default_factory=lambda: Gauge(
        'bot_queue_size',
        'Current queue size',
        ['type']
    ))

class MetricsManager:
    """Manages Prometheus metrics collection and reporting"""
    
    def __init__(self):
        self.metrics = BotMetrics()
        self._command_contexts: Dict[str, Any] = {}

    def record_latency(self, command: str, duration: float) -> None:
        """Record command execution latency"""
        self.metrics.command_latency.labels(command=command).observe(duration)

    def record_error(self, error_type: str, command: Optional[str] = None) -> None:
        """Record an error occurrence"""
        self.metrics.errors.labels(type=error_type).inc()
        if command:
            self.metrics.command_latency.labels(command=command).observe(float('inf'))

    def update_active_commands(self, delta: int = 1) -> None:
        """Update the number of active commands"""
        if delta > 0:
            self.metrics.active_commands.inc(delta)
        else:
            self.metrics.active_commands.dec(abs(delta))

    def update_stream_count(self, delta: int = 1) -> None:
        """Update the number of active streams"""
        if delta > 0:
            self.metrics.active_streams.inc(delta)
        else:
            self.metrics.active_streams.dec(abs(delta))

    def update_queue_size(self, queue_type: str, size: int) -> None:
        """Update queue size metric"""
        self.metrics.queue_size.labels(type=queue_type).set(size)

    def get_metrics(self) -> BotMetrics:
        """Get all registered metrics"""
        return self.metrics