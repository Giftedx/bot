"""Redis manager for data persistence"""
import json
import logging
from typing import Any, Dict, Optional
import redis
from redis.exceptions import ConnectionError as RedisConnectionError

logger = logging.getLogger('RedisManager')


class RedisManager:
    """Manages Redis connection and data operations"""

    def __init__(self) -> None:
        """Initialize Redis connection"""
        try:
            self.redis: Optional[redis.Redis] = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )
            self.redis.ping()  # Test connection
            logger.info("Connected to Redis")
        except RedisConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis = None

    def set(self, key: str, value: Any, expiry: Optional[int] = None) -> bool:
        """Set a key-value pair in Redis"""
        if not self.redis:
            logger.error("Redis not connected")
            return False

        try:
            serialized = (
                json.dumps(value) 
                if not isinstance(value, (str, int, float)) 
                else value
            )
            self.redis.set(key, serialized, ex=expiry)
            return True
        except Exception as e:
            logger.error(f"Error setting Redis key {key}: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """Get a value from Redis"""
        if not self.redis:
            logger.error("Redis not connected")
            return None

        try:
            value = self.redis.get(key)
            if value is None:
                return None
                
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Error getting Redis key {key}: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete a key from Redis"""
        if not self.redis:
            logger.error("Redis not connected")
            return False

        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error(f"Error deleting Redis key {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis"""
        if not self.redis:
            logger.error("Redis not connected")
            return False

        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            logger.error(f"Error checking Redis key {key}: {e}")
            return False

    def get_hash(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a hash from Redis"""
        if not self.redis:
            logger.error("Redis not connected")
            return None

        try:
            hash_data = self.redis.hgetall(key)
            if not hash_data:
                return None
                
            return {
                k: json.loads(v) 
                if isinstance(v, str) and v.startswith('{') 
                else v
                for k, v in hash_data.items()
            }
        except Exception as e:
            logger.error(f"Error getting Redis hash {key}: {e}")
            return None

    def set_hash(self, key: str, data: Dict[str, Any]) -> bool:
        """Set a hash in Redis"""
        if not self.redis:
            logger.error("Redis not connected")
            return False

        try:
            serialized = {
                k: (
                    json.dumps(v) 
                    if not isinstance(v, (str, int, float)) 
                    else v
                )
                for k, v in data.items()
            }
            self.redis.hmset(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Error setting Redis hash {key}: {e}")
            return False

    def close(self) -> None:
        """Close Redis connection"""
        if self.redis:
            self.redis.close()
            logger.info("Redis connection closed")
