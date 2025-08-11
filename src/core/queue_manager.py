from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


class QueuePriority(Enum):
    HIGH = 3
    MEDIUM = 2
    LOW = 1


@dataclass
class QueueItem:
    media_id: str
    requester_id: str
    timestamp: datetime
    priority: QueuePriority = QueuePriority.MEDIUM


class QueueManager:
    def __init__(self, max_length: int = 100, redis_manager: Optional[object] = None):
        self.max_length = max_length
        self.redis_manager = redis_manager
        self.queue: List[QueueItem] = []
        self.current_item: Optional[QueueItem] = None
        self._lock = asyncio.Lock()

    async def add(self, item: QueueItem) -> None:
        async with self._lock:
            if len(self.queue) >= self.max_length:
                self.queue.pop(0)
            self.queue.append(item)
            # Keep highest priority first, FIFO within same priority
            self.queue.sort(key=lambda i: (-i.priority.value, i.timestamp))

    async def get(self) -> Optional[QueueItem]:
        async with self._lock:
            if not self.queue:
                return None
            self.current_item = self.queue.pop(0)
            return self.current_item

    async def clear(self) -> None:
        async with self._lock:
            self.queue.clear()
            self.current_item = None