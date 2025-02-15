from typing import Any, Dict, Optional
import pytest
from datetime import datetime, timedelta
import time
from unittest.mock import Mock, AsyncMock, patch

from src.core.caching import CacheManager, CachePolicy, CacheEntry
from src.core.exceptions import CacheError

@pytest.fixture
def cache_manager() -> CacheManager:
    return CacheManager()

def test_basic_cache_operations(cache_manager: CacheManager) -> None:
    """Test basic cache set/get operations."""
    cache_manager.set("test_key", "test_value")
    assert cache_manager.get("test_key") == "test_value"
    assert cache_manager.exists("test_key")

def test_cache_expiration(cache_manager: CacheManager) -> None:
    """Test cache entry expiration."""
    cache_manager.set("expiring_key", "expiring_value", ttl_seconds=1)
    assert cache_manager.get("expiring_key") == "expiring_value"
    
    time.sleep(1.1)  # Wait for expiration
    assert cache_manager.get("expiring_key") is None

def test_cache_policy(cache_manager: CacheManager) -> None:
    """Test cache policy enforcement."""
    policy = CachePolicy(
        max_size=2,
        eviction_policy="lru"
    )
    cache_manager.set_policy(policy)
    
    cache_manager.set("key1", "value1")
    cache_manager.set("key2", "value2")
    cache_manager.set("key3", "value3")  # Should trigger eviction
    
    assert not cache_manager.exists("key1")  # Should be evicted
    assert cache_manager.exists("key2")
    assert cache_manager.exists("key3")

@pytest.mark.asyncio
async def test_async_cache_operations(cache_manager: CacheManager) -> None:
    """Test async cache operations."""
    async def expensive_operation() -> str:
        await asyncio.sleep(0.1)
        return "expensive_result"
    
    # First call should execute the operation
    result1 = await cache_manager.get_or_compute(
        "async_key",
        expensive_operation
    )
    assert result1 == "expensive_result"
    
    # Second call should return cached result
    result2 = await cache_manager.get_or_compute(
        "async_key",
        expensive_operation
    )
    assert result2 == "expensive_result"
    assert cache_manager.get_stats()["hits"] == 1

def test_cache_invalidation(cache_manager: CacheManager) -> None:
    """Test cache invalidation patterns."""
    cache_manager.set("key1", "value1")
    cache_manager.set("prefix:key2", "value2")
    cache_manager.set("prefix:key3", "value3")
    
    # Invalidate single key
    cache_manager.invalidate("key1")
    assert not cache_manager.exists("key1")
    
    # Invalidate by prefix
    cache_manager.invalidate_by_prefix("prefix:")
    assert not cache_manager.exists("prefix:key2")
    assert not cache_manager.exists("prefix:key3")

def test_cache_statistics(cache_manager: CacheManager) -> None:
    """Test cache statistics collection."""
    cache_manager.set("stats_key1", "value1")
    cache_manager.get("stats_key1")  # Hit
    cache_manager.get("missing_key")  # Miss
    
    stats = cache_manager.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["size"] == 1

def test_cache_serialization(cache_manager: CacheManager) -> None:
    """Test cache entry serialization."""
    complex_value = {
        "nested": {
            "data": [1, 2, 3],
            "date": datetime.now()
        }
    }
    
    cache_manager.set("complex_key", complex_value)
    retrieved = cache_manager.get("complex_key")
    
    assert retrieved["nested"]["data"] == [1, 2, 3]
    assert isinstance(retrieved["nested"]["date"], datetime)

def test_cache_error_handling(cache_manager: CacheManager) -> None:
    """Test cache error handling."""
    with pytest.raises(CacheError) as exc_info:
        cache_manager.set("", "invalid_key")  # Empty key
    assert "invalid key" in str(exc_info.value).lower()
    
    with pytest.raises(CacheError) as exc_info:
        cache_manager.set_policy(CachePolicy(max_size=-1))  # Invalid policy
    assert "invalid policy" in str(exc_info.value).lower()

if __name__ == "__main__":
    pytest.main()