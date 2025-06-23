"""Tests for the cache utility."""
import pytest
import time
from src.utils.cache import Cache, cached


def test_cache_set_get(cache):
    """Test basic cache set and get operations."""
    # Test with string value
    cache.set("test_key", "test_value")
    assert cache.get("test_key") == "test_value"

    # Test with dict value
    test_dict = {"key": "value", "number": 42}
    cache.set("dict_key", test_dict)
    assert cache.get("dict_key") == test_dict

    # Test with non-existent key
    assert cache.get("nonexistent") is None


def test_cache_ttl(cache):
    """Test cache TTL functionality."""
    # Set value with 1 second TTL
    cache.set("ttl_key", "ttl_value", ttl=1)
    assert cache.get("ttl_key") == "ttl_value"

    # Wait for TTL to expire
    time.sleep(1.1)
    assert cache.get("ttl_key") is None


def test_cache_delete(cache):
    """Test cache delete operation."""
    cache.set("delete_key", "delete_value")
    assert cache.get("delete_key") == "delete_value"

    cache.delete("delete_key")
    assert cache.get("delete_key") is None

    # Delete non-existent key should not raise error
    cache.delete("nonexistent")


def test_cache_clear(cache):
    """Test cache clear operation."""
    # Set multiple values
    cache.set("key1", "value1")
    cache.set("key2", "value2")

    cache.clear()
    assert cache.get("key1") is None
    assert cache.get("key2") is None


def test_cache_decorator():
    """Test cached decorator."""
    call_count = 0

    @cached(ttl=1)
    def test_function(arg1, arg2=None):
        nonlocal call_count
        call_count += 1
        return f"{arg1}-{arg2}"

    # First call should execute function
    result1 = test_function("test", arg2="value")
    assert result1 == "test-value"
    assert call_count == 1

    # Second call with same args should use cache
    result2 = test_function("test", arg2="value")
    assert result2 == "test-value"
    assert call_count == 1

    # Different args should execute function again
    result3 = test_function("test", arg2="different")
    assert result3 == "test-different"
    assert call_count == 2

    # Wait for TTL to expire
    time.sleep(1.1)

    # Should execute function again after TTL expires
    result4 = test_function("test", arg2="value")
    assert result4 == "test-value"
    assert call_count == 3


def test_cache_large_values(cache):
    """Test cache with large values."""
    large_data = "x" * 1024 * 1024  # 1MB string
    cache.set("large_key", large_data)
    assert cache.get("large_key") == large_data


def test_cache_invalid_json(cache, tmp_path):
    """Test cache behavior with invalid JSON data."""
    # Write invalid JSON directly to cache file
    cache_file = tmp_path / "cache" / "invalid.json"
    cache_file.parent.mkdir(exist_ok=True)
    cache_file.write_text("{invalid json")

    # Reading invalid cache should return None
    assert cache.get("invalid") is None


def test_cache_concurrent_access(cache):
    """Test cache with concurrent access patterns."""
    import threading
    import random

    def worker():
        for _ in range(100):
            key = f"key_{random.randint(1, 10)}"
            value = f"value_{random.randint(1, 10)}"
            if random.random() < 0.5:
                cache.set(key, value)
            else:
                cache.get(key)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # No exceptions should have been raised


@pytest.mark.asyncio
async def test_cache_async_decorator():
    """Test cached decorator with async functions."""
    call_count = 0

    @cached(ttl=1)
    async def test_async_function(arg):
        nonlocal call_count
        call_count += 1
        return f"async-{arg}"

    # First call
    result1 = await test_async_function("test")
    assert result1 == "async-test"
    assert call_count == 1

    # Cached call
    result2 = await test_async_function("test")
    assert result2 == "async-test"
    assert call_count == 1
