"""OSRS task manager implementation."""
from typing import Dict, List, Optional, Type
from datetime import datetime
import asyncio
import logging

from .task import Task, TaskStatus
from ..models.user import User


logger = logging.getLogger(__name__)


class TaskManager:
    """Manages multiple tasks for a user."""

    def __init__(self, user: User):
        """Initialize task manager for user."""
        self.user = user
        self._active_tasks: Dict[str, Task] = {}
        self._task_history: List[Task] = []
        self._running = False

    @property
    def active_tasks(self) -> Dict[str, Task]:
        """Get currently active tasks."""
        return self._active_tasks.copy()

    @property
    def task_history(self) -> List[Task]:
        """Get completed task history."""
        return self._task_history.copy()

    def add_task(self, task: Task) -> bool:
        """
        Add a new task.
        Returns True if successfully added and started.
        """
        # Check if task type is already running
        task_type = task.__class__.__name__
        if task_type in self._active_tasks:
            return False

        # Try to start the task
        if not task.start():
            return False

        # Add to active tasks
        self._active_tasks[task_type] = task
        return True

    def cancel_task(self, task_type: str) -> bool:
        """
        Cancel a running task.
        Returns True if successfully cancelled.
        """
        task = self._active_tasks.get(task_type)
        if not task:
            return False

        if task.cancel():
            self._task_history.append(task)
            del self._active_tasks[task_type]
            return True

        return False

    def get_task(self, task_type: str) -> Optional[Task]:
        """Get a task by type if it exists."""
        return self._active_tasks.get(task_type)

    async def start(self) -> None:
        """Start the task manager's update loop."""
        self._running = True
        while self._running:
            self._update()
            await asyncio.sleep(0.6)  # Game tick is 0.6 seconds

    def stop(self) -> None:
        """Stop the task manager's update loop."""
        self._running = False

    def _update(self) -> None:
        """Update all active tasks."""
        completed_tasks = []

        for task_type, task in self._active_tasks.items():
            try:
                # Update task state
                task.tick()

                # Check if task should complete
                if (task.status == TaskStatus.RUNNING and
                    task.end_time and
                    datetime.now() >= task.end_time):
                    if task.complete():
                        completed_tasks.append(task_type)
                        self._task_history.append(task)
                    else:
                        logger.error(f"Failed to complete task: {task}")

            except Exception as e:
                logger.error(f"Error updating task {task}: {e}")
                task.status = TaskStatus.FAILED
                completed_tasks.append(task_type)
                self._task_history.append(task)

        # Remove completed tasks
        for task_type in completed_tasks:
            del self._active_tasks[task_type]

    def __str__(self) -> str:
        """String representation of task manager state."""
        active = len(self._active_tasks)
        history = len(self._task_history)
        return f"TaskManager(active={active}, completed={history})" 