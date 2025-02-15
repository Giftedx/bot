import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional, TypeVar
from redis.asyncio import Redis
from redis.exceptions import RedisError
from datetime import datetime, timedelta

from src.core.exceptions import RedisConnectionError, RedisOperationError
from src.utils.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)
T = TypeVar('T')

class RedisKeys:
    """Redis key constants."""
    QUEUE_PREFIX = "media:queue:"
    CACHE_PREFIX = "cache:"
    RATE_LIMIT_PREFIX = "rate_limit:"
    STREAM_PREFIX = "stream:"

class RedisManager:
    """Redis connection and operations manager with circuit breaker pattern."""

    def __init__(
        self,
        redis_url: str,
        max_connections: int = 10,
        circuit_breaker_config: Optional[Dict[str, Any]] = None
    ):
        self._redis_url = redis_url
        self._redis: Optional[Redis] = None
        self._pool_lock = asyncio.Lock()
        self.keys = RedisKeys()
        
        # Configure circuit breaker
        cb_config = circuit_breaker_config or {}
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=cb_config.get('failure_threshold', 5),
            success_threshold=cb_config.get('success_threshold', 2),
            recovery_timeout=cb_config.get('recovery_timeout', 30.0),
            backoff_factor=cb_config.get('backoff_factor', 2.0),
            max_backoff=cb_config.get('max_backoff', 300.0),
            window_size=cb_config.get('window_size', 60)
        )

    async def _get_redis(self) -> Redis:
        """Get Redis connection with circuit breaker protection."""
        if not self._redis:
            async with self._pool_lock:
                if not self._redis:
                    try:
                        async def connect():
                            connection = Redis.from_url(self._redis_url)
                            await connection.ping()
                            return connection
                            
                        self._redis = await self._circuit_breaker.call(connect)
                    except Exception as e:
                        logger.error(f"Redis connection failed: {e}")
                        raise RedisConnectionError(f"Failed to connect: {e}")
        return self._redis

    async def execute(
        self,
        operation: str,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """Execute Redis operation with circuit breaker protection."""
        try:
            redis = await self._get_redis()
            async def run_operation():
                method = getattr(redis, operation)
                return await method(*args, **kwargs)
            
            return await self._circuit_breaker.call(run_operation)
        except RedisError as e:
            logger.error(f"Redis operation {operation} failed: {e}")
            raise RedisOperationError(f"Operation failed: {e}")

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    # Cache operations
    async def cache_get(self, key: str) -> Optional[T]:
        """Get cached value."""
        data = await self.execute('get', f"{self.keys.CACHE_PREFIX}{key}")
        return json.loads(data) if data else None

    async def cache_set(
        self,
        key: str,
        value: Any,
        expire: int = 3600
    ) -> None:
        """Set cached value with expiration."""
        data = json.dumps(value)
        await self.execute(
            'setex',
            f"{self.keys.CACHE_PREFIX}{key}",
            expire,
            data
        )

    # Queue operations
    async def queue_push(self, queue_name: str, item: Any) -> None:
        """Push item to queue."""
        await self.execute(
            'rpush',
            f"{self.keys.QUEUE_PREFIX}{queue_name}",
            json.dumps(item)
        )

    async def queue_pop(
        self,
        queue_name: str,
        timeout: int = 0
    ) -> Optional[T]:
        """Pop item from queue with optional timeout."""
        result = await self.execute(
            'blpop',
            f"{self.keys.QUEUE_PREFIX}{queue_name}",
            timeout
        )
        if result:
            return json.loads(result[1])
        return None

    # Rate limiting
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int
    ) -> bool:
        """Check rate limit."""
        redis_key = f"{self.keys.RATE_LIMIT_PREFIX}{key}"
        current = await self.execute('incr', redis_key)
        if current == 1:
            await self.execute('expire', redis_key, window)
        return current <= limit

    # Stream operations
    async def stream_add(
        self,
        stream: str,
        data: Dict[str, Any]
    ) -> str:
        """Add entry to stream."""
        return await self.execute(
            'xadd',
            f"{self.keys.STREAM_PREFIX}{stream}",
            '*',
            data
        )

    async def stream_read(
        self,
        stream: str,
        count: int = 100,
        block: int = 0
    ) -> List[Dict[str, Any]]:
        """Read from stream."""
        return await self.execute(
            'xread',
            count=count,
            block=block,
            streams=[f"{self.keys.STREAM_PREFIX}{stream}", '$']
        )

    # Health check
    async def ping(self) -> bool:
        """Check Redis connection health."""
        try:
            return await self.execute('ping') == b'PONG'
        except Exception:
            return False