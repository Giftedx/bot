from typing import Dict, List, Optional, Tuple
import random
from dataclasses import dataclass
from datetime import datetime

from .combat.monster_manager import MonsterDefinition

@dataclass
class SlayerTask:
    monster_id: int
    amount_assigned: int
    amount_remaining: int
    assigned_at: datetime
    completed_at: Optional[datetime] = None
    experience_gained: float = 0.0

class SlayerMaster:
    def __init__(
        self,
        name: str,
        level_req: int,
        task_range: Tuple[int, int],
        assignments: Dict[str, float]  # monster_id: weight
    ):
        self.name = name
        self.level_req = level_req
        self.task_range = task_range
        self.assignments = assignments
        
        # Normalize weights
        total_weight = sum(assignments.values())
        self.weights = {
            monster: weight / total_weight
            for monster, weight in assignments.items()
        }

class SlayerSystem:
    """Handles slayer tasks and rewards."""
    
    MASTERS = {
        'turael': SlayerMaster(
            name='Turael',
            level_req=1,
            task_range=(15, 25),
            assignments={
                'goblin': 6,
                'giant_rat': 6,
                'hill_giant': 4,
                'lesser_demon': 2
            }
        ),
        'mazchna': SlayerMaster(
            name='Mazchna',
            level_req=20,
            task_range=(30, 50),
            assignments={
                'hill_giant': 6,
                'lesser_demon': 5,
                'moss_giant': 5,
                'banshee': 4,
                'cave_crawler': 4
            }
        ),
        'vannaka': SlayerMaster(
            name='Vannaka',
            level_req=40,
            task_range=(40, 70),
            assignments={
                'lesser_demon': 8,
                'moss_giant': 7,
                'fire_giant': 6,
                'green_dragon': 5,
                'blue_dragon': 4
            }
        ),
        'chaeldar': SlayerMaster(
            name='Chaeldar',
            level_req=70,
            task_range=(60, 100),
            assignments={
                'fire_giant': 8,
                'greater_demon': 7,
                'black_demon': 6,
                'steel_dragon': 4,
                'aberrant_spectre': 5
            }
        ),
        'nieve': SlayerMaster(
            name='Nieve',
            level_req=85,
            task_range=(80, 150),
            assignments={
                'greater_demon': 9,
                'black_demon': 8,
                'steel_dragon': 6,
                'dark_beast': 5,
                'abyssal_demon': 7
            }
        ),
        'duradel': SlayerMaster(
            name='Duradel',
            level_req=100,
            task_range=(100, 200),
            assignments={
                'black_demon': 9,
                'dark_beast': 8,
                'abyssal_demon': 8,
                'kalphite_queen': 5,
                'king_black_dragon': 5
            }
        )
    }
    
    REWARDS = {
        # Points per task based on streak
        'points': {
            0: 0,    # First 4 tasks
            5: 15,   # Every 5th task
            10: 30,  # Every 10th task
            50: 50,  # Every 50th task
            100: 100,  # Every 100th task
            250: 200,  # Every 250th task
            1000: 500  # Every 1000th task
        },
        
        # Unlockable rewards
        'unlocks': {
            'broader_fletching': {
                'points': 300,
                'description': 'Ability to fletch broad bolts and arrows'
            },
            'slayer_ring': {
                'points': 300,
                'description': 'Ability to craft slayer rings'
            },
            'herb_sack': {
                'points': 750,
                'description': 'Store herbs in a special sack'
            },
            'rune_pouch': {
                'points': 1200,
                'description': 'Store runes in a special pouch'
            }
        }
    }
    
    def __init__(self):
        self.current_task: Optional[SlayerTask] = None
        self.task_streak: int = 0
        self.total_tasks: int = 0
        self.points: int = 0
        self.unlocks: List[str] = []
    
    def get_available_masters(self, slayer_level: int) -> List[SlayerMaster]:
        """Get all slayer masters available at given level."""
        return [
            master for master in self.MASTERS.values()
            if master.level_req <= slayer_level
        ]
    
    def assign_task(
        self,
        master_name: str,
        slayer_level: int,
        blocked_tasks: List[str] = None
    ) -> Optional[SlayerTask]:
        """Assign a new slayer task."""
        # Check if player already has a task
        if self.current_task and self.current_task.amount_remaining > 0:
            return None
            
        # Get master
        master = self.MASTERS.get(master_name.lower())
        if not master:
            return None
            
        # Check level requirement
        if slayer_level < master.level_req:
            return None
            
        # Get available assignments
        available = {
            monster: weight
            for monster, weight in master.weights.items()
            if monster not in (blocked_tasks or [])
        }
        
        if not available:
            return None
            
        # Choose monster
        monster_id = random.choices(
            list(available.keys()),
            weights=list(available.values())
        )[0]
        
        # Choose amount
        amount = random.randint(*master.task_range)
        
        # Create task
        self.current_task = SlayerTask(
            monster_id=monster_id,
            amount_assigned=amount,
            amount_remaining=amount,
            assigned_at=datetime.utcnow()
        )
        
        return self.current_task
    
    def record_kill(self, monster_id: str) -> Tuple[bool, float]:
        """Record a monster kill and return (task_complete, xp_gained)."""
        if not self.current_task or monster_id != self.current_task.monster_id:
            return False, 0
            
        # Update task progress
        self.current_task.amount_remaining -= 1
        
        # Calculate XP gained
        xp_gained = self._calculate_slayer_xp(monster_id)
        self.current_task.experience_gained += xp_gained
        
        # Check if task is complete
        if self.current_task.amount_remaining <= 0:
            self.current_task.completed_at = datetime.utcnow()
            self._complete_task()
            return True, xp_gained
            
        return False, xp_gained
    
    def cancel_task(self, points_cost: int = 30) -> bool:
        """Cancel current task for points."""
        if not self.current_task or self.points < points_cost:
            return False
            
        self.points -= points_cost
        self.current_task = None
        self.task_streak = 0
        return True
    
    def block_task(self, points_cost: int = 100) -> Optional[str]:
        """Block current task for points."""
        if not self.current_task or self.points < points_cost:
            return None
            
        self.points -= points_cost
        blocked_task = self.current_task.monster_id
        self.current_task = None
        return blocked_task
    
    def unlock_reward(self, reward_name: str) -> bool:
        """Unlock a reward with points."""
        reward = self.REWARDS['unlocks'].get(reward_name)
        if not reward or reward_name in self.unlocks or self.points < reward['points']:
            return False
            
        self.points -= reward['points']
        self.unlocks.append(reward_name)
        return True
    
    def _complete_task(self):
        """Handle task completion and rewards."""
        self.total_tasks += 1
        self.task_streak += 1
        
        # Award points based on streak
        points = 0
        for streak, reward in sorted(self.REWARDS['points'].items(), reverse=True):
            if self.total_tasks % streak == 0:
                points = reward
                break
                
        self.points += points
    
    def _calculate_slayer_xp(self, monster_id: str) -> float:
        """Calculate slayer XP for killing a monster."""
        # In a real implementation, this would look up the monster's slayer XP
        # For now, return a basic amount
        return 50.0  # Base XP per kill 