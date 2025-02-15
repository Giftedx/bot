"""Prometheus metrics collection for the application."""
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from prometheus_client import Counter, Histogram, Gauge, Summary, start_http_server
import time
from contextlib import contextmanager
from .logger import get_logger
from .config import config

logger = get_logger(__name__)

@dataclass
class RepositoryMetrics:
    """Metrics for repository operations."""
    # Search and parsing metrics
    search_latency: Histogram = field(default_factory=lambda: Histogram(
        'repo_search_latency_seconds',
        'Repository search operation latency',
        ['category']
    ))
    parse_errors: Counter = field(default_factory=lambda: Counter(
        'repo_parse_errors_total',
        'Number of repository parsing errors',
        ['source']
    ))
    
    # GitHub API metrics
    github_api_errors: Counter = field(default_factory=lambda: Counter(
        'github_api_errors_total',
        'Number of GitHub API errors',
        ['type']
    ))
    github_api_latency: Summary = field(default_factory=lambda: Summary(
        'github_api_latency_seconds',
        'GitHub API request latency',
        ['operation']
    ))
    api_rate_limit: Gauge = field(default_factory=lambda: Gauge(
        'github_api_rate_limit',
        'GitHub API rate limit status',
        ['type']
    ))
    
    # Repository metrics
    repositories_total: Gauge = field(default_factory=lambda: Gauge(
        'repositories_total',
        'Total number of repositories',
        ['category']
    ))
    repository_stars: Summary = field(default_factory=lambda: Summary(
        'repository_stars',
        'Repository star counts',
        ['category']
    ))
    metadata_updates: Counter = field(default_factory=lambda: Counter(
        'metadata_updates_total',
        'Number of repository metadata updates'
    ))
    
    # Cache metrics
    cache_hits: Counter = field(default_factory=lambda: Counter(
        'cache_hits_total',
        'Number of cache hits',
        ['type']
    ))
    cache_misses: Counter = field(default_factory=lambda: Counter(
        'cache_misses_total',
        'Number of cache misses',
        ['type']
    ))
    cache_size: Gauge = field(default_factory=lambda: Gauge(
        'cache_size_bytes',
        'Current cache size in bytes'
    ))
    
    # Task metrics
    task_latency: Summary = field(default_factory=lambda: Summary(
        'task_latency_seconds',
        'Task execution latency',
        ['name']
    ))
    task_errors: Counter = field(default_factory=lambda: Counter(
        'task_errors_total',
        'Number of task execution errors',
        ['name']
    ))
    active_tasks: Gauge = field(default_factory=lambda: Gauge(
        'active_tasks',
        'Number of currently active tasks',
        ['type']
    ))
    queue_size: Gauge = field(default_factory=lambda: Gauge(
        'queue_size',
        'Current queue size',
        ['type']
    ))
    
    # Health metrics
    service_health: Gauge = field(default_factory=lambda: Gauge(
        'service_health',
        'Service health status (1=healthy, 0=unhealthy)',
        ['service']
    ))
    health_check_latency: Summary = field(default_factory=lambda: Summary(
        'health_check_latency_seconds',
        'Health check execution latency',
        ['check']
    ))

class MetricsManager:
    """Manages application metrics collection and reporting."""
    
    def __init__(self, port: int = None):
        self._port = port or config.get('METRICS_PORT', 8000)
        self._started = False
        self.metrics = RepositoryMetrics()
        
        # Profiling metrics
        self.profile_duration = Summary('profile_duration_seconds', 'Duration of profiled operations',
                                     ['name'])
        self.profile_calls = Counter('profile_calls_total', 'Number of calls to profiled operations',
                                   ['name'])
        self.profile_time_per_call = Summary('profile_time_per_call_seconds', 
                                           'Average time per call for profiled operations',
                                           ['name'])
    
    def start(self) -> None:
        """Start the Prometheus metrics server."""
        if not self._started and config.get('ENABLE_METRICS'):
            try:
                start_http_server(self._port)
                self._started = True
                logger.info(f"Metrics server started on port {self._port}")
            except Exception as e:
                logger.error(f"Failed to start metrics server: {e}")
    
    @contextmanager
    def measure_latency(self, category: str, operation: str = "default"):
        """Measure operation latency."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            if category == "search":
                self.metrics.search_latency.labels(category=operation).observe(duration)
            elif category == "github_api":
                self.metrics.github_api_latency.labels(operation=operation).observe(duration)
            elif category == "task":
                self.metrics.task_latency.labels(name=operation).observe(duration)
            elif category == "health_check":
                self.metrics.health_check_latency.labels(check=operation).observe(duration)
    
    def record_parse_error(self, source: str) -> None:
        """Record a repository parsing error."""
        self.metrics.parse_errors.labels(source=source).inc()
    
    def record_github_error(self, error_type: str) -> None:
        """Record a GitHub API error."""
        self.metrics.github_api_errors.labels(type=error_type).inc()
    
    def update_repository_count(self, category: str, count: int) -> None:
        """Update repository count for a category."""
        self.metrics.repositories_total.labels(category=category).set(count)
    
    def record_repository_stars(self, category: str, stars: int) -> None:
        """Record repository star count."""
        self.metrics.repository_stars.labels(category=category).observe(stars)
    
    def record_metadata_update(self) -> None:
        """Record a successful metadata update."""
        self.metrics.metadata_updates.inc()
    
    def record_cache_operation(self, operation_type: str, hit: bool) -> None:
        """Record cache operation result."""
        if hit:
            self.metrics.cache_hits.labels(type=operation_type).inc()
        else:
            self.metrics.cache_misses.labels(type=operation_type).inc()
    
    def update_cache_size(self, size_bytes: int) -> None:
        """Update current cache size."""
        self.metrics.cache_size.set(size_bytes)
    
    def record_task_error(self, task_name: str) -> None:
        """Record a task execution error."""
        self.metrics.task_errors.labels(name=task_name).inc()
    
    def update_active_tasks(self, task_type: str, count: int) -> None:
        """Update number of active tasks."""
        self.metrics.active_tasks.labels(type=task_type).set(count)
    
    def update_queue_size(self, queue_type: str, size: int) -> None:
        """Update queue size metric."""
        self.metrics.queue_size.labels(type=queue_type).set(size)
    
    def update_service_health(self, service: str, healthy: int) -> None:
        """Update service health status."""
        self.metrics.service_health.labels(service=service).set(healthy)
    
    def update_rate_limit(self, limit_type: str, remaining: int, reset_time: int) -> None:
        """Update GitHub API rate limit metrics."""
        self.metrics.api_rate_limit.labels(type=f"{limit_type}_remaining").set(remaining)
        self.metrics.api_rate_limit.labels(type=f"{limit_type}_reset").set(reset_time)
    
    def record_profile_stats(self, name: str, duration: float, calls: int, time_per_call: float) -> None:
        """Record profiling statistics."""
        self.profile_duration.labels(name=name).observe(duration)
        self.profile_calls.labels(name=name).inc(calls)
        self.profile_time_per_call.labels(name=name).observe(time_per_call)

# Global metrics manager instance
metrics = MetricsManager() 