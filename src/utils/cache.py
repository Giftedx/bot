"""Caching system for improved performance."""
from typing import Any, Optional, Callable
from pathlib import Path
import json
import time
from functools import wraps
from .logger import get_logger
from .config import config

logger = get_logger(__name__)


class Cache:
    """Simple file-based cache with TTL support."""

    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or config.get("CACHE_DIR")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cleanup_cache()

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for key."""
        return self.cache_dir / f"{key}.json"

    def _cleanup_cache(self) -> None:
        """Remove expired cache entries."""
        current_time = time.time()
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file) as f:
                    data = json.load(f)
                if data.get("expires_at", 0) < current_time:
                    cache_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to cleanup cache file {cache_file}: {e}")

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        cache_file = self._get_cache_path(key)
        if not cache_file.exists():
            return None

        try:
            with open(cache_file) as f:
                data = json.load(f)

            # Check expiration
            if data.get("expires_at", 0) < time.time():
                cache_file.unlink()
                return None

            return data["value"]
        except Exception as e:
            logger.warning(f"Failed to read cache for {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Set value in cache with optional TTL."""
        if not config.get("ENABLE_CACHE"):
            return

        ttl = ttl or config.get("CACHE_EXPIRY")
        cache_file = self._get_cache_path(key)

        try:
            data = {"value": value, "expires_at": time.time() + ttl}
            with open(cache_file, "w") as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning(f"Failed to write cache for {key}: {e}")

    def delete(self, key: str) -> None:
        """Delete value from cache."""
        cache_file = self._get_cache_path(key)
        try:
            if cache_file.exists():
                cache_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to delete cache for {key}: {e}")

    def clear(self) -> None:
        """Clear all cache entries."""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")


def cached(ttl: Optional[int] = None, key_prefix: Optional[str] = None):
    """Decorator for caching function results."""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not config.get("ENABLE_CACHE"):
                return func(*args, **kwargs)

            # Generate cache key
            cache_key = f"{key_prefix or func.__name__}"
            if args:
                cache_key += f"_{str(args)}"
            if kwargs:
                cache_key += f"_{str(sorted(kwargs.items()))}"

            # Get cached value
            cache = Cache()
            result = cache.get(cache_key)

            if result is None:
                result = func(*args, **kwargs)
                cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


# Global cache instance
cache = Cache()
