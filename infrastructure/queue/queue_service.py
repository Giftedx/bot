from typing import Any, Dict, List, Optional, Callable, Awaitable
import json
import asyncio
import logging
from datetime import datetime
import uuid
from dataclasses import dataclass

from shared.utils.service_interface import BaseService
from shared.utils.common import json_dumps, json_loads

@dataclass
class Message:
    """Message structure for queue"""
    id: str
    topic: str
    payload: Dict[str, Any]
    timestamp: datetime
    retry_count: int = 0
    max_retries: int = 3
    delay_seconds: int = 0

class QueueService(BaseService):
    """Service for managing message queues"""
    
    def __init__(self, redis_config: Dict[str, str]):
        super().__init__("queue", "1.0.0")
        self.redis_config = redis_config
        self.redis = None
        self.logger = logging.getLogger(__name__)
        self.handlers: Dict[str, List[Callable[[Message], Awaitable[None]]]] = {}
        self.processing_tasks: List[asyncio.Task] = []
        self._should_process = False
    
    async def _init_dependencies(self) -> None:
        """Initialize Redis connection"""
        import redis
        self.redis = redis.Redis(
            host=self.redis_config['host'],
            port=int(self.redis_config['port']),
            db=int(self.redis_config['db']),
            password=self.redis_config['password'],
            decode_responses=True
        )
    
    async def _start_service(self) -> None:
        """Start the queue service"""
        try:
            self.redis.ping()
            self.logger.info("Queue service started")
            self._should_process = True
            # Start message processors for each topic
            for topic in self.handlers.keys():
                self.processing_tasks.append(
                    asyncio.create_task(self._process_queue(topic))
                )
        except Exception as e:
            self.record_error("startup", str(e))
            raise
    
    async def _stop_service(self) -> None:
        """Stop the queue service"""
        self._should_process = False
        # Wait for processing tasks to complete
        if self.processing_tasks:
            await asyncio.gather(*self.processing_tasks, return_exceptions=True)
        if self.redis:
            self.redis.close()
    
    async def _cleanup_resources(self) -> None:
        """Cleanup queue resources"""
        pass
    
    def register_handler(self, topic: str, handler: Callable[[Message], Awaitable[None]]):
        """Register a message handler for a topic"""
        if topic not in self.handlers:
            self.handlers[topic] = []
        self.handlers[topic].append(handler)
        self.logger.info(f"Registered handler for topic {topic}")
    
    async def publish(self, topic: str, payload: Dict[str, Any], 
                     delay_seconds: int = 0, max_retries: int = 3) -> str:
        """Publish a message to a topic"""
        message = Message(
            id=str(uuid.uuid4()),
            topic=topic,
            payload=payload,
            timestamp=datetime.utcnow(),
            max_retries=max_retries,
            delay_seconds=delay_seconds
        )
        
        try:
            if delay_seconds > 0:
                # Add to delayed queue
                score = datetime.utcnow().timestamp() + delay_seconds
                self.redis.zadd(
                    f"delayed:{topic}",
                    {json_dumps(message.__dict__): score}
                )
            else:
                # Add to main queue
                self.redis.lpush(
                    f"queue:{topic}",
                    json_dumps(message.__dict__)
                )
            
            self.logger.debug(f"Published message {message.id} to topic {topic}")
            return message.id
            
        except Exception as e:
            self.logger.error(f"Error publishing message to {topic}: {e}")
            raise
    
    async def _process_queue(self, topic: str):
        """Process messages for a topic"""
        while self._should_process:
            try:
                # Process delayed messages first
                await self._process_delayed_messages(topic)
                
                # Process main queue
                message_data = self.redis.brpop(f"queue:{topic}", timeout=1)
                if not message_data:
                    continue
                    
                message_dict = json_loads(message_data[1])
                message = Message(**message_dict)
                
                # Process message with all registered handlers
                await self._process_message(message)
                
            except Exception as e:
                self.logger.error(f"Error processing queue {topic}: {e}")
                await asyncio.sleep(1)  # Prevent tight loop on error
    
    async def _process_delayed_messages(self, topic: str):
        """Process messages in the delayed queue"""
        now = datetime.utcnow().timestamp()
        
        # Get messages that are ready to be processed
        ready_messages = self.redis.zrangebyscore(
            f"delayed:{topic}",
            0,
            now,
            withscores=True
        )
        
        for message_data, score in ready_messages:
            # Remove from delayed queue
            self.redis.zrem(f"delayed:{topic}", message_data)
            
            # Add to main queue
            self.redis.lpush(f"queue:{topic}", message_data)
    
    async def _process_message(self, message: Message):
        """Process a single message with all registered handlers"""
        if message.topic not in self.handlers:
            self.logger.warning(f"No handlers registered for topic {message.topic}")
            return
            
        for handler in self.handlers[message.topic]:
            try:
                await handler(message)
            except Exception as e:
                self.logger.error(f"Error processing message {message.id}: {e}")
                
                if message.retry_count < message.max_retries:
                    # Requeue with exponential backoff
                    message.retry_count += 1
                    delay = 2 ** message.retry_count
                    await self.publish(
                        message.topic,
                        message.payload,
                        delay_seconds=delay,
                        max_retries=message.max_retries
                    )
                else:
                    # Move to dead letter queue
                    self.redis.lpush(
                        f"dlq:{message.topic}",
                        json_dumps(message.__dict__)
                    )
    
    def get_queue_length(self, topic: str) -> int:
        """Get the number of messages in a queue"""
        try:
            return self.redis.llen(f"queue:{topic}")
        except Exception as e:
            self.logger.error(f"Error getting queue length for {topic}: {e}")
            return 0
    
    def get_delayed_count(self, topic: str) -> int:
        """Get the number of delayed messages"""
        try:
            return self.redis.zcard(f"delayed:{topic}")
        except Exception as e:
            self.logger.error(f"Error getting delayed count for {topic}: {e}")
            return 0
    
    def get_dlq_length(self, topic: str) -> int:
        """Get the number of messages in the dead letter queue"""
        try:
            return self.redis.llen(f"dlq:{topic}")
        except Exception as e:
            self.logger.error(f"Error getting DLQ length for {topic}: {e}")
            return 0
    
    def clear_queue(self, topic: str) -> bool:
        """Clear all messages from a queue"""
        try:
            self.redis.delete(f"queue:{topic}")
            self.redis.delete(f"delayed:{topic}")
            self.redis.delete(f"dlq:{topic}")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing queue {topic}: {e}")
            return False 