"""Game tick system for synchronizing OSRS mechanics."""

import asyncio
import time
from typing import Dict, List, Callable, Coroutine, Any
from dataclasses import dataclass
from enum import Enum

class TickPriority(Enum):
    """Priority levels for tick tasks."""
    MOVEMENT = 1
    COMBAT = 2
    SKILLS = 3
    WORLD = 4
    INTERFACE = 5

@dataclass
class TickTask:
    """Task to be executed on game ticks."""
    callback: Callable[[], Coroutine[Any, Any, None]]
    priority: TickPriority
    interval: int = 1  # Execute every N ticks

class GameTick:
    """Manages the OSRS game tick system."""
    
    # OSRS uses 0.6 second ticks
    TICK_LENGTH = 0.6
    
    def __init__(self):
        """Initialize the game tick system."""
        self.running = False
        self.current_tick = 0
        self.tasks: Dict[str, TickTask] = {}
        self.last_tick_time = 0
        
    async def start(self):
        """Start the game tick system."""
        self.running = True
        self.last_tick_time = time.time()
        
        while self.running:
            current_time = time.time()
            elapsed = current_time - self.last_tick_time
            
            if elapsed >= self.TICK_LENGTH:
                await self._process_tick()
                self.last_tick_time = current_time
            else:
                # Sleep for remaining time to next tick
                await asyncio.sleep(self.TICK_LENGTH - elapsed)
                
    async def stop(self):
        """Stop the game tick system."""
        self.running = False
        
    def register_task(self, task_id: str, callback: Callable[[], Coroutine[Any, Any, None]], 
                      priority: TickPriority, interval: int = 1):
        """Register a task to be executed on ticks.
        
        Args:
            task_id: Unique identifier for the task
            callback: Async function to call
            priority: Task priority level
            interval: Execute every N ticks
        """
        self.tasks[task_id] = TickTask(callback, priority, interval)
        
    def unregister_task(self, task_id: str):
        """Remove a registered task.
        
        Args:
            task_id: Task identifier to remove
        """
        self.tasks.pop(task_id, None)
        
    async def _process_tick(self):
        """Process a single game tick."""
        self.current_tick += 1
        
        # Sort tasks by priority
        sorted_tasks = sorted(
            self.tasks.items(),
            key=lambda x: x[1].priority.value
        )
        
        # Execute tasks in priority order
        for task_id, task in sorted_tasks:
            if self.current_tick % task.interval == 0:
                try:
                    await task.callback()
                except Exception as e:
                    # Log error but continue processing other tasks
                    print(f"Error in task {task_id}: {e}")
                    
    def get_tick_count(self) -> int:
        """Get the current tick count.
        
        Returns:
            Number of ticks since start
        """
        return self.current_tick
        
    def get_time_to_next_tick(self) -> float:
        """Get time until next tick.
        
        Returns:
            Seconds until next tick
        """
        current_time = time.time()
        elapsed = current_time - self.last_tick_time
        return max(0, self.TICK_LENGTH - elapsed) 