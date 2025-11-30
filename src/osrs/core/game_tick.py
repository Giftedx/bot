"""Game tick system for synchronizing OSRS mechanics."""

import asyncio
import time
from typing import Dict, Callable, Coroutine, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TickPriority(Enum):
    """Priority levels for tick tasks.

    Lower values indicate higher execution priority.
    """

    MOVEMENT = 1
    COMBAT = 2
    SKILLS = 3
    WORLD = 4
    INTERFACE = 5


@dataclass
class TickTask:
    """Task to be executed on game ticks.

    Attributes:
        callback (Callable): The async function to execute.
        priority (TickPriority): The execution order priority.
        interval (int): Execution frequency (every N ticks). Defaults to 1.
    """

    callback: Callable[[], Coroutine[Any, Any, None]]
    priority: TickPriority
    interval: int = 1


class GameTick:
    """Manages the OSRS game tick system.

    This system simulates the 0.6s game tick cycle of Old School RuneScape,
    executing registered tasks in priority order.
    """

    # OSRS uses 0.6 second ticks
    TICK_LENGTH = 0.6

    def __init__(self) -> None:
        """Initialize the game tick system."""
        self.running: bool = False
        self.current_tick: int = 0
        self.tasks: Dict[str, TickTask] = {}
        self.last_tick_time: float = 0.0

    async def start(self) -> None:
        """Start the game tick loop.

        This method runs indefinitely while `self.running` is True,
        executing tasks every 0.6 seconds.
        """
        self.running = True
        self.last_tick_time = time.time()

        while self.running:
            current_time = time.time()
            elapsed = current_time - self.last_tick_time

            if elapsed >= self.TICK_LENGTH:
                await self._process_tick()
                # Compensate for drift, but don't spiral if we are very behind
                # Just reset the anchor time if we are more than one tick behind
                if elapsed > self.TICK_LENGTH * 2:
                    self.last_tick_time = current_time
                else:
                    self.last_tick_time += self.TICK_LENGTH
            else:
                # Sleep for remaining time to next tick
                await asyncio.sleep(self.TICK_LENGTH - elapsed)

    async def stop(self) -> None:
        """Stop the game tick loop."""
        self.running = False

    def register_task(
        self,
        task_id: str,
        callback: Callable[[], Coroutine[Any, Any, None]],
        priority: TickPriority,
        interval: int = 1,
    ) -> None:
        """Register a task to be executed on ticks.

        Args:
            task_id (str): Unique identifier for the task.
            callback (Callable): Async function to call.
            priority (TickPriority): Task priority level.
            interval (int, optional): Execute every N ticks. Defaults to 1.
        """
        self.tasks[task_id] = TickTask(callback, priority, interval)

    def unregister_task(self, task_id: str) -> None:
        """Remove a registered task.

        Args:
            task_id (str): Task identifier to remove.
        """
        self.tasks.pop(task_id, None)

    async def _process_tick(self) -> None:
        """Process a single game tick.

        Increments the tick counter and executes eligible tasks in priority order.
        Exceptions in tasks are logged but do not halt the tick.
        """
        self.current_tick += 1

        # Sort tasks by priority
        sorted_tasks: List[Tuple[str, TickTask]] = sorted(
            self.tasks.items(), key=lambda x: x[1].priority.value
        )

        # Execute tasks in priority order
        for task_id, task in sorted_tasks:
            if self.current_tick % task.interval == 0:
                try:
                    await task.callback()
                except Exception as e:
                    # Log error but continue processing other tasks
                    logger.error(f"Error in task {task_id}: {e}", exc_info=True)

    def get_tick_count(self) -> int:
        """Get the current tick count.

        Returns:
            int: Number of ticks since start.
        """
        return self.current_tick

    def get_time_to_next_tick(self) -> float:
        """Get time until next tick.

        Returns:
            float: Seconds until next tick.
        """
        current_time = time.time()
        # Calculate time based on the scheduled next tick
        next_tick_time = self.last_tick_time + self.TICK_LENGTH
        remaining = next_tick_time - current_time
        return max(0.0, remaining)
