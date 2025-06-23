"""Background task management system."""
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar
from dataclasses import dataclass, field
import asyncio
import time
from datetime import datetime, timedelta
from .logger import get_logger
from .metrics import metrics
from .exceptions import AppError

logger = get_logger(__name__)
T = TypeVar("T")


@dataclass
class Task:
    """Background task information."""

    id: str
    coroutine: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    error: Optional[Exception] = None
    result: Any = None
    status: str = "pending"
    retries: int = 0
    max_retries: int = 3
    retry_delay: float = 1.0


class TaskManager:
    """Manages background tasks and their execution."""

    def __init__(self, max_concurrent: int = 10, max_queue_size: int = 100):
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        self.tasks: Dict[str, Task] = {}
        self._active_tasks: Set[str] = set()
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._workers: List[asyncio.Task] = []
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        """Start the task manager."""
        self._stop_event.clear()
        self._workers = [asyncio.create_task(self._worker()) for _ in range(self.max_concurrent)]
        logger.info(f"Started {len(self._workers)} task workers")

    async def stop(self) -> None:
        """Stop the task manager."""
        self._stop_event.set()

        # Wait for workers to finish
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
            self._workers.clear()

        logger.info("Task manager stopped")

    async def submit(self, task_id: str, coroutine: Callable, *args, **kwargs) -> str:
        """Submit a task for execution."""
        if task_id in self.tasks:
            raise AppError(f"Task {task_id} already exists")

        if self._queue.full():
            raise AppError("Task queue is full")

        task = Task(id=task_id, coroutine=coroutine, args=args, kwargs=kwargs)

        self.tasks[task_id] = task
        await self._queue.put(task_id)

        metrics.update_queue_size("tasks", self._queue.qsize())
        logger.debug(f"Submitted task {task_id}")

        return task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task information."""
        return self.tasks.get(task_id)

    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Task:
        """Wait for a task to complete."""
        start_time = time.time()
        task = self.get_task(task_id)

        if not task:
            raise AppError(f"Task {task_id} not found")

        while task.status in ("pending", "running"):
            if timeout and time.time() - start_time > timeout:
                raise asyncio.TimeoutError(f"Task {task_id} timed out")

            await asyncio.sleep(0.1)
            task = self.get_task(task_id)

        return task

    async def _worker(self) -> None:
        """Task worker process."""
        while not self._stop_event.is_set():
            try:
                # Get next task
                try:
                    task_id = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                task = self.tasks[task_id]
                task.status = "running"
                task.start_time = datetime.now()
                self._active_tasks.add(task_id)

                # Execute task
                try:
                    with metrics.measure_latency("task_execution"):
                        task.result = await task.coroutine(*task.args, **task.kwargs)
                    task.status = "completed"

                except Exception as e:
                    logger.error(f"Task {task_id} failed: {e}")
                    task.error = e

                    # Handle retries
                    if task.retries < task.max_retries:
                        task.retries += 1
                        task.status = "pending"
                        await asyncio.sleep(task.retry_delay * task.retries)
                        await self._queue.put(task_id)
                    else:
                        task.status = "failed"

                finally:
                    task.completion_time = datetime.now()
                    self._active_tasks.remove(task_id)
                    self._queue.task_done()
                    metrics.update_queue_size("tasks", self._queue.qsize())

            except Exception as e:
                logger.error(f"Worker error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get task manager statistics."""
        now = datetime.now()
        return {
            "total_tasks": len(self.tasks),
            "active_tasks": len(self._active_tasks),
            "queue_size": self._queue.qsize(),
            "status_counts": {
                status: len([t for t in self.tasks.values() if t.status == status])
                for status in ("pending", "running", "completed", "failed")
            },
            "completed_last_hour": len(
                [
                    t
                    for t in self.tasks.values()
                    if t.completion_time and t.completion_time > now - timedelta(hours=1)
                ]
            ),
        }


# Global task manager instance
task_manager = TaskManager()
