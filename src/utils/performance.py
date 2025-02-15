"""Performance monitoring utilities."""
import time
import functools
from typing import Any, Callable, TypeVar, ParamSpec, Coroutine
from prometheus_client import Histogram, Counter, Gauge

# Global metrics registry
METRICS = {
    'command_latency': Histogram(
        'command_latency_seconds',
        'Command execution latency in seconds',
        ['command_name']
    ),
    'command_errors': Counter(
        'bot_command_errors_total',
        'Command error count',
        ['command']
    ),
    'active_commands': Gauge(
        'bot_active_commands',
        'Number of active commands'
    )
}

P = ParamSpec('P')
T = TypeVar('T')

def measure_latency(func: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, Coroutine[Any, Any, T]]:
    """Decorator to measure coroutine execution time.
    
    Args:
        func: The coroutine function to measure
    Returns:
        Wrapped coroutine function that measures execution time
    """
    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start_time = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration = time.perf_counter() - start_time
            METRICS['command_latency'].labels(command_name=func.__name__).observe(duration)
    return wrapper