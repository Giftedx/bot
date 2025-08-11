"""Performance profiling utilities."""
from typing import Dict, Optional
from dataclasses import dataclass, field
import cProfile
import pstats
import io
import time
import asyncio
from contextlib import contextmanager
from functools import wraps
from .logger import get_logger
from .metrics import metrics

logger = get_logger(__name__)


@dataclass
class ProfileResult:
    """Profile result data."""

    name: str
    total_time: float
    calls: int
    time_per_call: float
    cumulative_time: float
    callers: Dict[str, int] = field(default_factory=dict)
    callees: Dict[str, int] = field(default_factory=dict)


class Profiler:
    """Performance profiler."""

    def __init__(self):
        self._active_profiles: Dict[str, cProfile.Profile] = {}
        self._results: Dict[str, ProfileResult] = {}

    @contextmanager
    def profile(self, name: str):
        """Context manager for profiling a block of code."""
        profiler = cProfile.Profile()
        self._active_profiles[name] = profiler

        start_time = time.time()
        profiler.enable()

        try:
            yield
        finally:
            profiler.disable()
            duration = time.time() - start_time

            # Process results
            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
            ps.print_stats()

            # Parse profiler output
            stats = ps.stats
            if stats:
                # Get the main function stats
                main_func = list(stats.items())[0]
                cc, nc, tt, ct, callers = main_func[1]

                self._results[name] = ProfileResult(
                    name=name,
                    total_time=tt,
                    calls=nc,
                    time_per_call=tt / nc if nc > 0 else 0,
                    cumulative_time=ct,
                    callers={str(caller): count for caller, count in callers.items()},
                    callees={
                        str(callee): stats[callee][1]
                        for callee in stats
                        if main_func[0] in stats[callee][4]
                    },
                )

                # Record metrics
                metrics.record_profile_stats(
                    name, duration=duration, calls=nc, time_per_call=tt / nc if nc > 0 else 0
                )

            del self._active_profiles[name]

    def profile_function(self, name: Optional[str] = None):
        """Decorator for profiling a function."""

        def decorator(func):
            profile_name = name or func.__name__

            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.profile(profile_name):
                    return func(*args, **kwargs)

            return wrapper

        return decorator

    async def profile_async(self, name: str, coro):
        """Profile an async coroutine."""
        with self.profile(name):
            return await coro

    def get_results(self, name: Optional[str] = None) -> Dict[str, ProfileResult]:
        """Get profiling results."""
        if name:
            return {name: self._results[name]} if name in self._results else {}
        return self._results

    def print_results(self, name: Optional[str] = None) -> None:
        """Print profiling results."""
        results = self.get_results(name)

        for profile_name, result in results.items():
            print(f"\nProfile Results for {profile_name}:")
            print(f"Total time: {result.total_time:.6f}s")
            print(f"Calls: {result.calls}")
            print(f"Time per call: {result.time_per_call:.6f}s")
            print(f"Cumulative time: {result.cumulative_time:.6f}s")

            if result.callers:
                print("\nCallers:")
                for caller, count in result.callers.items():
                    print(f"  {caller}: {count} calls")

            if result.callees:
                print("\nCallees:")
                for callee, count in result.callees.items():
                    print(f"  {callee}: {count} calls")

    def clear(self) -> None:
        """Clear profiling results."""
        self._results.clear()


class AsyncProfiler:
    """Async-aware performance profiler."""

    def __init__(self):
        self._profiler = Profiler()
        self._active_tasks: Dict[str, asyncio.Task] = {}

    @contextmanager
    async def profile(self, name: str):
        """Context manager for profiling async code."""
        task = asyncio.current_task()
        if task:
            self._active_tasks[name] = task

        with self._profiler.profile(name):
            try:
                yield
            finally:
                if name in self._active_tasks:
                    del self._active_tasks[name]

    def profile_function(self, name: Optional[str] = None):
        """Decorator for profiling an async function."""

        def decorator(func):
            profile_name = name or func.__name__

            @wraps(func)
            async def wrapper(*args, **kwargs):
                async with self.profile(profile_name):
                    return await func(*args, **kwargs)

            return wrapper

        return decorator

    def get_results(self, name: Optional[str] = None) -> Dict[str, ProfileResult]:
        """Get profiling results."""
        return self._profiler.get_results(name)

    def print_results(self, name: Optional[str] = None) -> None:
        """Print profiling results."""
        self._profiler.print_results(name)

    def clear(self) -> None:
        """Clear profiling results."""
        self._profiler.clear()
        self._active_tasks.clear()


# Global profiler instances
profiler = Profiler()
async_profiler = AsyncProfiler()
