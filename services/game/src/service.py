from typing import Dict, List, Optional, Any
import logging
import math
import random
from datetime import datetime

from shared.utils.service_interface import BaseService
from infrastructure.database.database_service import DatabaseService
from infrastructure.cache.cache_service import CacheService
from infrastructure.database.models import User, PlayerState
from .models import (
    GameState, Position, CombatStats, Equipment, InventoryItem, BankItem,
    Skills, SkillType, CombatStyle, AttackType, QuestStatus, ActionResult,
    CombatBonuses, calculate_max_hit, calculate_hit_chance, PRAYER_BONUSES
)

class GameService(BaseService):
    """Service for managing game state and mechanics"""
    
    def __init__(self,
                 database_service: DatabaseService,
                 cache_service: CacheService):
        super().__init__("game", "1.0.0")
        self.db = database_service
        self.cache = cache_service
        self.logger = logging.getLogger(__name__)
        
        # Cache settings
        self.state_cache_ttl = 300  # 5 minutes
        
    async def _init_dependencies(self) -> None:
        """Initialize service dependencies"""
        pass
    
    async def _start_service(self) -> None:
        """Start the game service"""
        self.logger.info("Game service started")
    
    async def _stop_service(self) -> None:
        """Stop the game service"""
        self.logger.info("Game service stopped")
    
    async def _cleanup_resources(self) -> None:
        """Cleanup service resources"""
        pass
    
    async def get_game_state(self, user_id: str) -> Optional[GameState]:
        """Get current game state for a user"""
        # Check cache first
        cache_key = f"game_state:{user_id}"
        state = self.cache.get(cache_key)
        if state:
            return GameState(**state)
            
        # Get from database
        player_state = self.db.get_all(PlayerState, {"user_id": int(user_id)})
        if not player_state:
            return None
            
        state = player_state[0]
        
        # Convert to game state
        game_state = GameState(
            user_id=user_id,
            position=Position(**state.position) if state.position else Position(0, 0),
            combat_stats=CombatStats(**state.combat_stats),
            equipment=Equipment(**state.equipment),
            inventory=[InventoryItem(**item) for item in state.inventory],
            bank=[BankItem(**item) for item in state.bank],
            skills=Skills(
                levels={SkillType(k): v for k, v in state.skills.items()},
                experience={SkillType(k): v for k, v in state.experience.items()}
            ),
            quest_progress={k: QuestStatus(v) for k, v in state.quest_progress.items()},
            achievement_progress=state.achievement_progress,
            is_busy=state.is_busy,
            current_action=state.current_action,
            last_action=state.last_action
        )
        
        # Cache state
        self.cache.set(cache_key, game_state.__dict__, self.state_cache_ttl)
        
        return game_state
    
    async def update_game_state(self, state: GameState) -> bool:
        """Update game state"""
        try:
            # Update database
            player_state = self.db.get_all(PlayerState, {"user_id": int(state.user_id)})[0]
            
            updates = {
                "position": state.position.__dict__,
                "combat_stats": state.combat_stats.__dict__,
                "equipment": state.equipment.__dict__,
                "inventory": [item.__dict__ for item in state.inventory],
                "bank": [item.__dict__ for item in state.bank],
                "skills": {k.value: v for k, v in state.skills.levels.items()},
                "experience": {k.value: v for k, v in state.skills.experience.items()},
                "quest_progress": {k: v.value for k, v in state.quest_progress.items()},
                "achievement_progress": state.achievement_progress,
                "is_busy": state.is_busy,
                "current_action": state.current_action,
                "last_action": state.last_action
            }
            
            self.db.update(player_state, updates)
            
            # Update cache
            cache_key = f"game_state:{state.user_id}"
            self.cache.set(cache_key, state.__dict__, self.state_cache_ttl)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating game state: {e}")
            return False
    
    async def perform_action(self, user_id: str, action: str, 
                           params: Optional[Dict[str, Any]] = None) -> ActionResult:
        """Perform a game action"""
        state = await self.get_game_state(user_id)
        if not state:
            return ActionResult(
                success=False,
                message="Player state not found"
            )
            
        if state.is_busy:
            return ActionResult(
                success=False,
                message=f"Already busy with {state.current_action}"
            )
            
        # Handle different action types
        try:
            if action.startswith("combat_"):
                return await self._handle_combat_action(state, action, params)
            elif action.startswith("skill_"):
                return await self._handle_skill_action(state, action, params)
            elif action.startswith("item_"):
                return await self._handle_item_action(state, action, params)
            elif action.startswith("move_"):
                return await self._handle_movement_action(state, action, params)
            else:
                return ActionResult(
                    success=False,
                    message=f"Unknown action: {action}"
                )
                
        except Exception as e:
            self.logger.error(f"Error performing action {action}: {e}")
            return ActionResult(
                success=False,
                message="Action failed"
            )
    
    async def _handle_combat_action(self, state: GameState, action: str,
                                  params: Optional[Dict[str, Any]]) -> ActionResult:
        """Handle combat-related actions"""
        if action == "combat_attack":
            if not params or "target" not in params:
                return ActionResult(
                    success=False,
                    message="No target specified"
                )
                
            # Calculate hit
            target = params["target"]
            combat_style = params.get("style", CombatStyle.ACCURATE)
            attack_type = params.get("type", AttackType.SLASH)
            
            # Get equipment bonuses
            bonuses = self._calculate_equipment_bonuses(state.equipment)
            
            # Calculate max hit
            max_hit = calculate_max_hit(
                state.combat_stats.strength,
                bonuses.melee_strength,
                PRAYER_BONUSES.get(params.get("prayer"), 1.0)
            )
            
            # Calculate hit chance
            hit_chance = calculate_hit_chance(
                state.combat_stats.attack,
                bonuses.attack_slash,
                target["defence"],
                target["defence_bonus"],
                PRAYER_BONUSES.get(params.get("prayer"), 1.0)
            )
            
            # Determine if hit lands
            if random.random() <= hit_chance:
                damage = random.randint(0, max_hit)
                xp_gained = {
                    SkillType.HITPOINTS: math.floor(damage * 1.33),
                    SkillType.ATTACK: math.floor(damage * 4)
                }
                
                return ActionResult(
                    success=True,
                    message=f"Hit {damage} damage",
                    experience_gained=xp_gained
                )
            else:
                return ActionResult(
                    success=True,
                    message="Missed",
                    experience_gained={
                        SkillType.HITPOINTS: 0,
                        SkillType.ATTACK: 0
                    }
                )
    
    async def _handle_skill_action(self, state: GameState, action: str,
                                 params: Optional[Dict[str, Any]]) -> ActionResult:
        """Handle skill-related actions"""
        skill_type = SkillType(action.split("_")[1])
        
        if not params or "object" not in params:
            return ActionResult(
                success=False,
                message="No object specified"
            )
            
        obj = params["object"]
        required_level = obj.get("level", 1)
        
        # Check level requirement
        if state.skills.levels[skill_type] < required_level:
            return ActionResult(
                success=False,
                message=f"Requires {skill_type.value} level {required_level}"
            )
            
        # Calculate success chance
        success_chance = self._calculate_success_chance(
            state.skills.levels[skill_type],
            required_level
        )
        
        if random.random() <= success_chance:
            xp_gained = {skill_type: obj.get("xp", 0)}
            items_gained = [InventoryItem(
                item_id=obj.get("product", ""),
                quantity=1,
                slot=self._find_free_inventory_slot(state)
            )]
            
            return ActionResult(
                success=True,
                message=f"Successfully performed {action}",
                experience_gained=xp_gained,
                items_gained=items_gained
            )
        else:
            return ActionResult(
                success=True,
                message="Failed to perform action"
            )
    
    async def _handle_item_action(self, state: GameState, action: str,
                                params: Optional[Dict[str, Any]]) -> ActionResult:
        """Handle item-related actions"""
        if not params or "item" not in params:
            return ActionResult(
                success=False,
                message="No item specified"
            )
            
        item = params["item"]
        
        if action == "item_equip":
            # Check if item is in inventory
            inv_item = next((i for i in state.inventory 
                           if i.item_id == item["id"]), None)
            if not inv_item:
                return ActionResult(
                    success=False,
                    message="Item not in inventory"
                )
                
            # Update equipment and inventory
            slot = item["slot"]
            setattr(state.equipment, slot, item["id"])
            state.inventory.remove(inv_item)
            
            await self.update_game_state(state)
            
            return ActionResult(
                success=True,
                message=f"Equipped {item['name']}"
            )
            
        elif action == "item_unequip":
            # Check if slot is free in inventory
            if len(state.inventory) >= 28:
                return ActionResult(
                    success=False,
                    message="Inventory full"
                )
                
            # Update equipment and inventory
            slot = item["slot"]
            current_item = getattr(state.equipment, slot)
            if not current_item:
                return ActionResult(
                    success=False,
                    message="Nothing to unequip"
                )
                
            setattr(state.equipment, slot, None)
            state.inventory.append(InventoryItem(
                item_id=current_item,
                quantity=1,
                slot=self._find_free_inventory_slot(state)
            ))
            
            await self.update_game_state(state)
            
            return ActionResult(
                success=True,
                message=f"Unequipped {item['name']}"
            )
    
    async def _handle_movement_action(self, state: GameState, action: str,
                                   params: Optional[Dict[str, Any]]) -> ActionResult:
        """Handle movement-related actions"""
        if not params or "position" not in params:
            return ActionResult(
                success=False,
                message="No position specified"
            )
            
        target = Position(**params["position"])
        
        # Calculate distance
        distance = math.sqrt(
            (target.x - state.position.x) ** 2 +
            (target.y - state.position.y) ** 2
        )
        
        # Update position
        state.position = target
        await self.update_game_state(state)
        
        return ActionResult(
            success=True,
            message=f"Moved {distance:.1f} tiles"
        )
    
    def _calculate_equipment_bonuses(self, equipment: Equipment) -> CombatBonuses:
        """Calculate combat bonuses from equipment"""
        # This would use item stats from a database
        # For now, return default bonuses
        return CombatBonuses()
    
    def _calculate_success_chance(self, level: int, required: int) -> float:
        """Calculate chance of success for a skill action"""
        if level >= required + 15:
            return 1.0
        return 0.5 + (level - required) * 0.03
    
    def _find_free_inventory_slot(self, state: GameState) -> int:
        """Find first free inventory slot"""
        used_slots = {item.slot for item in state.inventory}
        for slot in range(28):
            if slot not in used_slots:
                return slot
        return -1 