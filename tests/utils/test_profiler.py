"""Tests for the profiler utility."""
import pytest
import asyncio
import time
from src.utils.profiler import Profiler, AsyncProfiler, ProfileResult

def test_profiler_context_manager():
    """Test profiler context manager."""
    profiler = Profiler()
    
    with profiler.profile("test_operation"):
        time.sleep(0.1)  # Simulate work
    
    results = profiler.get_results("test_operation")
    assert len(results) == 1
    result = results["test_operation"]
    
    assert result.name == "test_operation"
    assert result.total_time >= 0.1
    assert result.calls > 0
    assert result.time_per_call > 0

def test_profiler_function_decorator():
    """Test profiler function decorator."""
    profiler = Profiler()
    
    @profiler.profile_function("decorated_func")
    def test_function():
        time.sleep(0.1)
        return "result"
    
    result = test_function()
    assert result == "result"
    
    results = profiler.get_results("decorated_func")
    assert len(results) == 1
    profile = results["decorated_func"]
    
    assert profile.total_time >= 0.1
    assert profile.calls == 1

def test_profiler_nested_calls():
    """Test profiler with nested function calls."""
    profiler = Profiler()
    
    def inner_function():
        with profiler.profile("inner"):
            time.sleep(0.1)
    
    with profiler.profile("outer"):
        inner_function()
        time.sleep(0.1)
    
    results = profiler.get_results()
    assert len(results) == 2
    
    outer = results["outer"]
    inner = results["inner"]
    
    assert outer.total_time >= 0.2  # Both sleeps
    assert inner.total_time >= 0.1  # Inner sleep only
    assert "inner" in str(outer.callees)

def test_profiler_clear():
    """Test clearing profiler results."""
    profiler = Profiler()
    
    with profiler.profile("test"):
        time.sleep(0.1)
    
    assert len(profiler.get_results()) == 1
    profiler.clear()
    assert len(profiler.get_results()) == 0

@pytest.mark.asyncio
async def test_async_profiler():
    """Test async profiler functionality."""
    profiler = AsyncProfiler()
    
    async def async_operation():
        await asyncio.sleep(0.1)
        return "async result"
    
    async with profiler.profile("async_op"):
        result = await async_operation()
    
    assert result == "async result"
    
    results = profiler.get_results("async_op")
    assert len(results) == 1
    profile = results["async_op"]
    
    assert profile.total_time >= 0.1
    assert profile.calls > 0

@pytest.mark.asyncio
async def test_async_profiler_decorator():
    """Test async profiler decorator."""
    profiler = AsyncProfiler()
    
    @profiler.profile_function("async_func")
    async def test_async_function():
        await asyncio.sleep(0.1)
        return "async result"
    
    result = await test_async_function()
    assert result == "async result"
    
    results = profiler.get_results("async_func")
    assert len(results) == 1
    profile = results["async_func"]
    
    assert profile.total_time >= 0.1
    assert profile.calls == 1

def test_profile_result_dataclass():
    """Test ProfileResult dataclass functionality."""
    result = ProfileResult(
        name="test",
        total_time=1.0,
        calls=5,
        time_per_call=0.2,
        cumulative_time=1.5,
        callers={"caller": 2},
        callees={"callee": 3}
    )
    
    assert result.name == "test"
    assert result.total_time == 1.0
    assert result.calls == 5
    assert result.time_per_call == 0.2
    assert result.cumulative_time == 1.5
    assert result.callers == {"caller": 2}
    assert result.callees == {"callee": 3}

def test_profiler_multiple_instances():
    """Test using multiple profiler instances."""
    profiler1 = Profiler()
    profiler2 = Profiler()
    
    with profiler1.profile("test1"):
        time.sleep(0.1)
    
    with profiler2.profile("test2"):
        time.sleep(0.1)
    
    results1 = profiler1.get_results()
    results2 = profiler2.get_results()
    
    assert len(results1) == 1
    assert len(results2) == 1
    assert "test1" in results1
    assert "test2" in results2
    assert "test1" not in results2
    assert "test2" not in results1 