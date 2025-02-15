"""Retry decorator with backoff support."""
from typing import Any, Callable, Optional, Type, Union, Tuple
from functools import wraps
import asyncio
import random
import time
from datetime import datetime
from .logger import get_logger
from .metrics import metrics
from .exceptions import AppError

logger = get_logger(__name__)

def retry(
    max_attempts: int = 3,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    backoff_base: float = 2.0,
    backoff_max: float = 60.0,
    jitter: bool = True,
    metric_name: Optional[str] = None
):
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        exceptions: Exception(s) to catch and retry on
        backoff_base: Base for exponential backoff
        backoff_max: Maximum backoff time in seconds
        jitter: Whether to add random jitter to backoff
        metric_name: Optional metric name for tracking retries
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            attempt = 0
            last_error = None
            
            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                    
                except exceptions as e:
                    attempt += 1
                    last_error = e
                    
                    if attempt == max_attempts:
                        if metric_name:
                            metrics.record_error(f"{metric_name}_max_retries")
                        raise
                        
                    # Calculate backoff time
                    backoff = min(
                        backoff_base ** (attempt - 1),
                        backoff_max
                    )
                    
                    # Add jitter if enabled
                    if jitter:
                        backoff *= (0.5 + random.random())
                        
                    if metric_name:
                        metrics.record_retry(metric_name)
                        
                    logger.warning(
                        f"Retry {attempt}/{max_attempts} for {func.__name__} "
                        f"after {backoff:.1f}s: {str(e)}"
                    )
                    
                    await asyncio.sleep(backoff)
                    
            # Should never reach here
            raise last_error
            
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            attempt = 0
            last_error = None
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    attempt += 1
                    last_error = e
                    
                    if attempt == max_attempts:
                        if metric_name:
                            metrics.record_error(f"{metric_name}_max_retries")
                        raise
                        
                    # Calculate backoff time
                    backoff = min(
                        backoff_base ** (attempt - 1),
                        backoff_max
                    )
                    
                    # Add jitter if enabled
                    if jitter:
                        backoff *= (0.5 + random.random())
                        
                    if metric_name:
                        metrics.record_retry(metric_name)
                        
                    logger.warning(
                        f"Retry {attempt}/{max_attempts} for {func.__name__} "
                        f"after {backoff:.1f}s: {str(e)}"
                    )
                    
                    time.sleep(backoff)
                    
            # Should never reach here
            raise last_error
            
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

def circuit_breaker(
    failure_threshold: int = 5,
    reset_timeout: float = 60.0,
    metric_name: Optional[str] = None
):
    """
    Circuit breaker decorator.
    
    Args:
        failure_threshold: Number of failures before opening circuit
        reset_timeout: Time in seconds before attempting to close circuit
        metric_name: Optional metric name for tracking circuit state
    """
    def decorator(func: Callable) -> Callable:
        # Circuit state
        failures = 0
        last_failure = None
        is_open = False
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            nonlocal failures, last_failure, is_open
            
            # Check if circuit is open
            if is_open:
                if last_failure and (time.time() - last_failure) > reset_timeout:
                    # Try to close circuit
                    is_open = False
                    failures = 0
                    if metric_name:
                        metrics.record_circuit_state(metric_name, "half-open")
                else:
                    if metric_name:
                        metrics.record_error(f"{metric_name}_circuit_open")
                    raise AppError("Circuit breaker is open")
            
            try:
                result = await func(*args, **kwargs)
                # Success, reset failure count
                failures = 0
                is_open = False
                if metric_name:
                    metrics.record_circuit_state(metric_name, "closed")
                return result
                
            except Exception as e:
                failures += 1
                last_failure = time.time()
                
                if failures >= failure_threshold:
                    is_open = True
                    if metric_name:
                        metrics.record_circuit_state(metric_name, "open")
                    
                if metric_name:
                    metrics.record_error(f"{metric_name}_failure")
                    
                raise
                
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            nonlocal failures, last_failure, is_open
            
            # Check if circuit is open
            if is_open:
                if last_failure and (time.time() - last_failure) > reset_timeout:
                    # Try to close circuit
                    is_open = False
                    failures = 0
                    if metric_name:
                        metrics.record_circuit_state(metric_name, "half-open")
                else:
                    if metric_name:
                        metrics.record_error(f"{metric_name}_circuit_open")
                    raise AppError("Circuit breaker is open")
            
            try:
                result = func(*args, **kwargs)
                # Success, reset failure count
                failures = 0
                is_open = False
                if metric_name:
                    metrics.record_circuit_state(metric_name, "closed")
                return result
                
            except Exception as e:
                failures += 1
                last_failure = time.time()
                
                if failures >= failure_threshold:
                    is_open = True
                    if metric_name:
                        metrics.record_circuit_state(metric_name, "open")
                    
                if metric_name:
                    metrics.record_error(f"{metric_name}_failure")
                    
                raise
                
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator 