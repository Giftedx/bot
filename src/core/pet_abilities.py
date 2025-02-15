from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from datetime import datetime, timedelta
import random

from .pet_system import Pet, PetOrigin, PetRarity
from ..features.pets.event_system import EventManager, EventType, GameEvent

class AbilityType(Enum):
    PASSIVE = "passive"
    ACTIVE = "active"
    ULTIMATE = "ultimate"

class AbilityTarget(Enum):
    SELF = "self"
    OPPONENT = "opponent"
    BOTH = "both"
    TEAM = "team"

class AbilityTrigger(Enum):
    ON_ATTACK = "on_attack"
    ON_DEFEND = "on_defend"
    ON_TURN_START = "on_turn_start"
    ON_TURN_END = "on_turn_end"
    ON_BATTLE_START = "on_battle_start"
    ON_BATTLE_END = "on_battle_end"
    ON_LEVEL_UP = "on_level_up"
    MANUAL = "manual"

class AbilityEffect(Enum):
    DAMAGE = "damage"
    HEAL = "heal"
    BUFF = "buff"
    DEBUFF = "debuff"
    SHIELD = "shield"
    STUN = "stun"
    DRAIN = "drain"
    REFLECT = "reflect"

class PetAbility:
    def __init__(
        self,
        name: str,
        description: str,
        ability_type: AbilityType,
        effect: AbilityEffect,
        target: AbilityTarget,
        trigger: AbilityTrigger,
        base_value: float,
        cooldown: int,  # in seconds
        level_requirement: int = 1,
        energy_cost: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.description = description
        self.ability_type = ability_type
        self.effect = effect
        self.target = target
        self.trigger = trigger
        self.base_value = base_value
        self.cooldown = cooldown
        self.level_requirement = level_requirement
        self.energy_cost = energy_cost
        self.metadata = metadata or {}
        self.last_used: Optional[datetime] = None

    def can_use(self, pet: Pet) -> bool:
        """Check if the ability can be used"""
        if pet.stats.level < self.level_requirement:
            return False
            
        if self.last_used:
            time_since_use = (datetime.utcnow() - self.last_used).total_seconds()
            if time_since_use < self.cooldown:
                return False
                
        return True

    def calculate_value(self, pet: Pet) -> float:
        """Calculate the actual effect value based on pet stats"""
        base = self.base_value
        level_bonus = (pet.stats.level / 50) * 0.5  # Up to 50% bonus at level 50
        loyalty_bonus = (pet.stats.loyalty / 100) * 0.2  # Up to 20% bonus at max loyalty
        
        if self.effect in [AbilityEffect.DAMAGE, AbilityEffect.HEAL]:
            stat_bonus = pet.stats.skill_levels["special"] / 100  # 1% per special level
        else:
            stat_bonus = 0
            
        return base * (1 + level_bonus + loyalty_bonus + stat_bonus)

class AbilityRegistry:
    def __init__(self):
        self.abilities: Dict[str, PetAbility] = {}
        self._init_default_abilities()
        
    def _init_default_abilities(self) -> None:
        """Initialize default abilities"""
        # OSRS-inspired abilities
        self.register_ability(PetAbility(
            name="Dragon Breath",
            description="Unleash a powerful breath attack",
            ability_type=AbilityType.ACTIVE,
            effect=AbilityEffect.DAMAGE,
            target=AbilityTarget.OPPONENT,
            trigger=AbilityTrigger.MANUAL,
            base_value=50.0,
            cooldown=30,
            level_requirement=20,
            energy_cost=25,
            metadata={"origin": PetOrigin.OSRS}
        ))
        
        self.register_ability(PetAbility(
            name="Prayer Shield",
            description="Create a protective shield that reduces damage",
            ability_type=AbilityType.ACTIVE,
            effect=AbilityEffect.SHIELD,
            target=AbilityTarget.SELF,
            trigger=AbilityTrigger.MANUAL,
            base_value=0.3,  # 30% damage reduction
            cooldown=45,
            level_requirement=25,
            energy_cost=30,
            metadata={"origin": PetOrigin.OSRS}
        ))
        
        # Pokemon-inspired abilities
        self.register_ability(PetAbility(
            name="Thunder Strike",
            description="Strike with electric energy",
            ability_type=AbilityType.ACTIVE,
            effect=AbilityEffect.DAMAGE,
            target=AbilityTarget.OPPONENT,
            trigger=AbilityTrigger.MANUAL,
            base_value=40.0,
            cooldown=20,
            level_requirement=15,
            energy_cost=20,
            metadata={"origin": PetOrigin.POKEMON}
        ))
        
        self.register_ability(PetAbility(
            name="Heal Pulse",
            description="Restore health over time",
            ability_type=AbilityType.ACTIVE,
            effect=AbilityEffect.HEAL,
            target=AbilityTarget.SELF,
            trigger=AbilityTrigger.MANUAL,
            base_value=30.0,
            cooldown=40,
            level_requirement=18,
            energy_cost=25,
            metadata={"origin": PetOrigin.POKEMON}
        ))
        
        # Cross-system abilities
        self.register_ability(PetAbility(
            name="System Sync",
            description="Synchronize with pets from other systems for increased power",
            ability_type=AbilityType.ULTIMATE,
            effect=AbilityEffect.BUFF,
            target=AbilityTarget.TEAM,
            trigger=AbilityTrigger.ON_BATTLE_START,
            base_value=0.2,  # 20% stat boost
            cooldown=120,
            level_requirement=30,
            energy_cost=50,
            metadata={"cross_system": True}
        ))

    def register_ability(self, ability: PetAbility) -> None:
        """Register a new ability"""
        self.abilities[ability.name] = ability

    def get_abilities_for_pet(self, pet: Pet) -> List[PetAbility]:
        """Get all abilities available for a pet"""
        available = []
        for ability in self.abilities.values():
            if pet.stats.level >= ability.level_requirement:
                if "origin" in ability.metadata:
                    if ability.metadata["origin"] == pet.origin:
                        available.append(ability)
                elif ability.metadata.get("cross_system", False):
                    available.append(ability)
        return available

class AbilityManager:
    def __init__(self, event_manager: Optional[EventManager] = None):
        self.registry = AbilityRegistry()
        self.event_manager = event_manager
        self.active_effects: Dict[str, List[Dict[str, Any]]] = {}  # pet_id -> active effects

    def use_ability(self, pet: Pet, ability_name: str, 
                   target: Optional[Pet] = None) -> Dict[str, Any]:
        """Use a pet ability"""
        ability = self.registry.abilities.get(ability_name)
        if not ability:
            return {"success": False, "message": f"Unknown ability: {ability_name}"}
            
        if not ability.can_use(pet):
            return {
                "success": False,
                "message": "Ability cannot be used (level requirement or cooldown)"
            }
            
        effect_value = ability.calculate_value(pet)
        ability.last_used = datetime.utcnow()
        
        result = {
            "success": True,
            "ability_name": ability_name,
            "effect_type": ability.effect.value,
            "effect_value": effect_value,
            "target": ability.target.value
        }
        
        # Apply immediate effects
        if ability.effect == AbilityEffect.DAMAGE and target:
            # Apply damage
            result["damage_dealt"] = effect_value
            
        elif ability.effect == AbilityEffect.HEAL:
            # Apply healing
            result["healing_done"] = effect_value
            
        elif ability.effect in [AbilityEffect.BUFF, AbilityEffect.DEBUFF, AbilityEffect.SHIELD]:
            # Add to active effects
            duration = 3  # Default 3 turns
            if "duration" in ability.metadata:
                duration = ability.metadata["duration"]
                
            effect = {
                "name": ability_name,
                "type": ability.effect.value,
                "value": effect_value,
                "duration": duration,
                "turns_remaining": duration
            }
            
            target_id = target.pet_id if target else pet.pet_id
            if target_id not in self.active_effects:
                self.active_effects[target_id] = []
            self.active_effects[target_id].append(effect)
            
            result["effect_duration"] = duration
        
        # Emit ability used event
        if self.event_manager:
            self.event_manager.emit(GameEvent(
                type=EventType.ABILITY_USED,
                user_id=str(pet.owner_id),
                timestamp=datetime.utcnow(),
                data={
                    "pet_id": pet.pet_id,
                    "ability_name": ability_name,
                    "effect_type": ability.effect.value,
                    "effect_value": effect_value,
                    "target_id": target.pet_id if target else pet.pet_id
                }
            ))
            
        return result

    def get_active_effects(self, pet: Pet) -> List[Dict[str, Any]]:
        """Get all active effects on a pet"""
        return self.active_effects.get(pet.pet_id, [])

    def update_effects(self, pet: Pet) -> List[Dict[str, Any]]:
        """Update active effects (reduce duration, remove expired)"""
        if pet.pet_id not in self.active_effects:
            return []
            
        active = self.active_effects[pet.pet_id]
        updated = []
        expired = []
        
        for effect in active:
            effect["turns_remaining"] -= 1
            if effect["turns_remaining"] > 0:
                updated.append(effect)
            else:
                expired.append(effect)
                
        self.active_effects[pet.pet_id] = updated
        return expired

    def calculate_effect_modifiers(self, pet: Pet) -> Dict[str, float]:
        """Calculate total effect modifiers from active effects"""
        modifiers = {
            "damage": 1.0,
            "healing": 1.0,
            "defense": 1.0
        }
        
        for effect in self.get_active_effects(pet):
            if effect["type"] == AbilityEffect.BUFF.value:
                for stat in modifiers:
                    modifiers[stat] *= (1 + effect["value"])
            elif effect["type"] == AbilityEffect.DEBUFF.value:
                for stat in modifiers:
                    modifiers[stat] *= (1 - effect["value"])
            elif effect["type"] == AbilityEffect.SHIELD.value:
                modifiers["defense"] *= (1 + effect["value"])
                
        return modifiers 