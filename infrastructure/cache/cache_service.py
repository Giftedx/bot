from typing import Any, Dict, List, Optional, Union
import json
import redis
from datetime import datetime, timedelta
import logging

from shared.utils.service_interface import BaseService
from shared.utils.common import json_dumps, json_loads

class CacheService(BaseService):
    """Service for managing Redis cache operations"""
    
    def __init__(self, redis_config: Dict[str, str]):
        super().__init__("cache", "1.0.0")
        self.redis_config = redis_config
        self.client = None
        self.logger = logging.getLogger(__name__)
        
        # Default TTLs
        self.default_ttl = 3600  # 1 hour
        self.session_ttl = 86400  # 24 hours
        self.token_ttl = 300  # 5 minutes
    
    async def _init_dependencies(self) -> None:
        """Initialize Redis connection"""
        self.client = redis.Redis(
            host=self.redis_config['host'],
            port=int(self.redis_config['port']),
            db=int(self.redis_config['db']),
            password=self.redis_config['password'],
            decode_responses=True
        )
    
    async def _start_service(self) -> None:
        """Start the cache service"""
        try:
            self.client.ping()
            self.logger.info("Redis connection established")
        except redis.ConnectionError as e:
            self.record_error("connection", str(e))
            raise
    
    async def _stop_service(self) -> None:
        """Stop the cache service"""
        if self.client:
            self.client.close()
            self.logger.info("Redis connection closed")
    
    async def _cleanup_resources(self) -> None:
        """Cleanup cache resources"""
        pass
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a cache key with optional TTL"""
        try:
            serialized = json_dumps(value)
            return self.client.set(
                key,
                serialized,
                ex=ttl or self.default_ttl
            )
        except Exception as e:
            self.logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a cache key"""
        try:
            value = self.client.get(key)
            if value is None:
                return default
            return json_loads(value)
        except Exception as e:
            self.logger.error(f"Error getting cache key {key}: {e}")
            return default
    
    def delete(self, key: str) -> bool:
        """Delete a cache key"""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            self.logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists"""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            self.logger.error(f"Error checking cache key {key}: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter"""
        try:
            return self.client.incrby(key, amount)
        except Exception as e:
            self.logger.error(f"Error incrementing cache key {key}: {e}")
            return None
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on a key"""
        try:
            return bool(self.client.expire(key, ttl))
        except Exception as e:
            self.logger.error(f"Error setting expiration for key {key}: {e}")
            return False
    
    def clear_namespace(self, namespace: str) -> bool:
        """Clear all keys in a namespace"""
        try:
            keys = self.client.keys(f"{namespace}:*")
            if keys:
                return bool(self.client.delete(*keys))
            return True
        except Exception as e:
            self.logger.error(f"Error clearing namespace {namespace}: {e}")
            return False
    
    # Session management
    def set_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Store session data"""
        return self.set(f"session:{session_id}", data, self.session_ttl)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        return self.get(f"session:{session_id}")
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session data"""
        return self.delete(f"session:{session_id}")
    
    # Token management
    def store_token(self, token: str, user_id: str) -> bool:
        """Store a token with user ID"""
        return self.set(f"token:{token}", user_id, self.token_ttl)
    
    def get_token_user(self, token: str) -> Optional[str]:
        """Get user ID for a token"""
        return self.get(f"token:{token}")
    
    def invalidate_token(self, token: str) -> bool:
        """Invalidate a token"""
        return self.delete(f"token:{token}")
    
    # Rate limiting
    def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check if rate limit is exceeded"""
        current = self.increment(f"ratelimit:{key}")
        if current == 1:
            self.expire(f"ratelimit:{key}", window)
        return current <= limit if current else False
    
    # Pub/Sub
    def publish(self, channel: str, message: Any) -> int:
        """Publish a message to a channel"""
        try:
            return self.client.publish(channel, json_dumps(message))
        except Exception as e:
            self.logger.error(f"Error publishing to channel {channel}: {e}")
            return 0
    
    def subscribe(self, channel: str) -> Any:
        """Subscribe to a channel"""
        try:
            pubsub = self.client.pubsub()
            pubsub.subscribe(channel)
            return pubsub
        except Exception as e:
            self.logger.error(f"Error subscribing to channel {channel}: {e}")
            return None 