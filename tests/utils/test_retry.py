"""Tests for the retry decorator."""
import pytest
import asyncio
import time
from src.utils.retry import retry, circuit_breaker
from src.utils.exceptions import AppError

def test_retry_sync():
    """Test retry decorator with synchronous functions."""
    attempts = 0
    
    @retry(max_attempts=3, exceptions=ValueError)
    def failing_function():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("Test error")
        return "success"
    
    result = failing_function()
    assert result == "success"
    assert attempts == 3

def test_retry_max_attempts():
    """Test retry decorator max attempts."""
    attempts = 0
    
    @retry(max_attempts=3, exceptions=ValueError)
    def always_fails():
        nonlocal attempts
        attempts += 1
        raise ValueError("Always fails")
    
    with pytest.raises(ValueError):
        always_fails()
    assert attempts == 3

def test_retry_exception_types():
    """Test retry decorator with different exception types."""
    attempts = 0
    
    @retry(max_attempts=3, exceptions=(ValueError, TypeError))
    def mixed_exceptions():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ValueError("First error")
        if attempts == 2:
            raise TypeError("Second error")
        return "success"
    
    result = mixed_exceptions()
    assert result == "success"
    assert attempts == 3

@pytest.mark.asyncio
async def test_retry_async():
    """Test retry decorator with async functions."""
    attempts = 0
    
    @retry(max_attempts=3, exceptions=ValueError)
    async def failing_async():
        nonlocal attempts
        attempts += 1
        await asyncio.sleep(0.1)
        if attempts < 3:
            raise ValueError("Test error")
        return "success"
    
    result = await failing_async()
    assert result == "success"
    assert attempts == 3

def test_retry_backoff():
    """Test retry decorator backoff timing."""
    attempts = 0
    start_time = time.time()
    
    @retry(
        max_attempts=3,
        exceptions=ValueError,
        backoff_base=2.0,
        backoff_max=4.0,
        jitter=False
    )
    def backoff_test():
        nonlocal attempts
        attempts += 1
        raise ValueError("Test error")
    
    with pytest.raises(ValueError):
        backoff_test()
    
    duration = time.time() - start_time
    # First retry after 2s, second retry after 4s
    assert 6.0 <= duration <= 7.0

@pytest.mark.asyncio
async def test_circuit_breaker():
    """Test circuit breaker decorator."""
    failures = 0
    
    @circuit_breaker(failure_threshold=2, reset_timeout=1.0)
    async def failing_service():
        nonlocal failures
        failures += 1
        raise ValueError("Service error")
    
    # First two calls should just raise the error
    for _ in range(2):
        with pytest.raises(ValueError):
            await failing_service()
    
    # Third call should raise circuit breaker error
    with pytest.raises(AppError, match="Circuit breaker is open"):
        await failing_service()
    
    # Wait for circuit to reset
    await asyncio.sleep(1.1)
    
    # Should try again and fail with original error
    with pytest.raises(ValueError):
        await failing_service()

@pytest.mark.asyncio
async def test_circuit_breaker_recovery():
    """Test circuit breaker recovery."""
    failures = 0
    
    @circuit_breaker(failure_threshold=2, reset_timeout=1.0)
    async def recovering_service():
        nonlocal failures
        failures += 1
        if failures <= 2:
            raise ValueError("Initial failures")
        return "recovered"
    
    # First two calls fail
    for _ in range(2):
        with pytest.raises(ValueError):
            await recovering_service()
    
    # Circuit is now open
    with pytest.raises(AppError, match="Circuit breaker is open"):
        await recovering_service()
    
    # Wait for reset
    await asyncio.sleep(1.1)
    
    # Service has recovered
    result = await recovering_service()
    assert result == "recovered"

def test_retry_with_metric():
    """Test retry decorator with metric tracking."""
    attempts = 0
    
    @retry(max_attempts=3, exceptions=ValueError, metric_name="test_retry")
    def failing_function():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("Test error")
        return "success"
    
    result = failing_function()
    assert result == "success"
    assert attempts == 3
    # Metric verification would go here if we had access to metrics

@pytest.mark.asyncio
async def test_circuit_breaker_with_metric():
    """Test circuit breaker with metric tracking."""
    failures = 0
    
    @circuit_breaker(
        failure_threshold=2,
        reset_timeout=1.0,
        metric_name="test_circuit"
    )
    async def failing_service():
        nonlocal failures
        failures += 1
        raise ValueError("Service error")
    
    # First two calls should fail normally
    for _ in range(2):
        with pytest.raises(ValueError):
            await failing_service()
    
    # Circuit should be open
    with pytest.raises(AppError):
        await failing_service()
    # Metric verification would go here 