from typing import Optional
from .redis_cache import RedisCache

class CacheFactory:
    """Factory for creating cache instances."""
    
    _redis_instance: Optional[RedisCache] = None
    
    @classmethod
    def get_redis_cache(cls, redis_url: str) -> RedisCache:
        """Get or create Redis cache instance.
        
        Args:
            redis_url: Redis connection URL
            
        Returns:
            Redis cache instance
        """
        if not cls._redis_instance:
            cls._redis_instance = RedisCache(redis_url)
        return cls._redis_instance 