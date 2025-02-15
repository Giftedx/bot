import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock
from src.utils.circuit_breaker import CircuitBreaker, CircuitBreakerError, CircuitState

@pytest.fixture
def circuit_breaker():
    return CircuitBreaker(
        failure_threshold=3,
        success_threshold=2,
        recovery_timeout=1.0,
        backoff_factor=2.0,
        max_backoff=4.0,
        window_size=10
    )

@pytest.mark.asyncio
async def test_initial_state(circuit_breaker):
    """Test initial circuit breaker state."""
    assert circuit_breaker.state == CircuitState.CLOSED

@pytest.mark.asyncio
async def test_successful_calls(circuit_breaker):
    """Test successful function calls."""
    mock_func = AsyncMock(return_value="success")
    
    result = await circuit_breaker.call(mock_func, "arg1", kwarg1="value1")
    assert result == "success"
    assert circuit_breaker.state == CircuitState.CLOSED
    mock_func.assert_called_once_with("arg1", kwarg1="value1")

@pytest.mark.asyncio
async def test_failure_threshold(circuit_breaker):
    """Test circuit opens after reaching failure threshold."""
    mock_func = AsyncMock(side_effect=Exception("test error"))
    
    for _ in range(3):  # Hit failure threshold
        with pytest.raises(Exception):
            await circuit_breaker.call(mock_func)
    
    assert circuit_breaker.state == CircuitState.OPEN
    
    with pytest.raises(CircuitBreakerError) as exc_info:
        await circuit_breaker.call(mock_func)
    assert "Circuit breaker is open" in str(exc_info.value)
    assert exc_info.value.retry_after > 0

@pytest.mark.asyncio
async def test_recovery_attempt(circuit_breaker):
    """Test recovery attempt after timeout."""
    mock_func = AsyncMock(side_effect=[Exception("error")] * 3 + ["success"])
    
    # Trigger circuit open
    for _ in range(3):
        with pytest.raises(Exception):
            await circuit_breaker.call(mock_func)
    
    assert circuit_breaker.state == CircuitState.OPEN
    
    # Wait for recovery timeout
    await asyncio.sleep(1.1)
    
    # Should transition to half-open and succeed
    result = await circuit_breaker.call(mock_func)
    assert result == "success"
    assert circuit_breaker.state == CircuitState.HALF_OPEN

@pytest.mark.asyncio
async def test_sliding_window(circuit_breaker):
    """Test sliding window failure counting."""
    mock_func = AsyncMock()
    current_time = datetime.now()
    
    # Simulate old failures outside window
    circuit_breaker._failure_times = [
        current_time - timedelta(seconds=15)
        for _ in range(5)
    ]
    
    # Add new failure
    mock_func.side_effect = Exception("test error")
    with pytest.raises(Exception):
        await circuit_breaker.call(mock_func)
    
    # Should only count failures within window
    assert len(circuit_breaker._failure_times) == 1
    assert circuit_breaker.state == CircuitState.CLOSED

@pytest.mark.asyncio
async def test_exponential_backoff(circuit_breaker):
    """Test exponential backoff timing."""
    mock_func = AsyncMock(side_effect=Exception("test error"))
    
    # Trigger circuit open
    for _ in range(3):
        with pytest.raises(Exception):
            await circuit_breaker.call(mock_func)
    
    # Check increasing backoff times
    retry_times = []
    for _ in range(3):
        with pytest.raises(CircuitBreakerError) as exc_info:
            await circuit_breaker.call(mock_func)
        retry_times.append(exc_info.value.retry_after)
        await asyncio.sleep(0.1)
    
    # Each retry should have increasing backoff
    assert retry_times[1] > retry_times[0]
    assert retry_times[2] > retry_times[1]

@pytest.mark.asyncio
async def test_success_threshold_recovery(circuit_breaker):
    """Test recovery after meeting success threshold."""
    mock_func = AsyncMock(side_effect=[Exception("error")] * 3 + ["success"] * 2)
    
    # Trigger circuit open
    for _ in range(3):
        with pytest.raises(Exception):
            await circuit_breaker.call(mock_func)
    
    await asyncio.sleep(1.1)  # Wait for recovery timeout
    
    # Two successful calls needed to close circuit
    result1 = await circuit_breaker.call(mock_func)
    assert result1 == "success"
    assert circuit_breaker.state == CircuitState.HALF_OPEN
    
    result2 = await circuit_breaker.call(mock_func)
    assert result2 == "success"
    assert circuit_breaker.state == CircuitState.CLOSED
