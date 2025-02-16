from typing import Any, Optional
import redis
import json
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis cache implementation for the Discord application."""
    
    def __init__(self, redis_url: str):
        """Initialize Redis cache connection.
        
        Args:
            redis_url: Redis connection URL (redis://host:port)
        """
        self.redis = redis.from_url(redis_url)
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if exists, None otherwise
        """
        try:
            value = self.redis.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
            
    def set(self, key: str, value: Any, expire: Optional[timedelta] = None) -> bool:
        """Set cache value with optional expiration.
        
        Args:
            key: Cache key
            value: Value to cache
            expire: Optional expiration time
            
        Returns:
            True if successful, False otherwise
        """
        try:
            serialized = json.dumps(value)
            if expire:
                return bool(self.redis.setex(key, expire, serialized))
            return bool(self.redis.set(key, serialized))
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
            
    def delete(self, key: str) -> bool:
        """Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
            
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter by amount.
        
        Args:
            key: Counter key
            amount: Amount to increment by
            
        Returns:
            New counter value or None if error
        """
        try:
            return self.redis.incr(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing key {key}: {e}")
            return None
            
    def rate_limit_check(self, key: str, limit: int, window: timedelta) -> bool:
        """Check if rate limit is exceeded.
        
        Args:
            key: Rate limit key
            limit: Maximum allowed in window
            window: Time window
            
        Returns:
            True if limit exceeded, False otherwise
        """
        try:
            current = self.increment(key)
            if current == 1:
                self.redis.expire(key, int(window.total_seconds()))
            return bool(current and current > limit)
        except Exception as e:
            logger.error(f"Error checking rate limit for {key}: {e}")
            return False 