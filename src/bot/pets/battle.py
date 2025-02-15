"""Pet battle system implementation."""
import random
from typing import Optional, Tuple

from src.bot.pets.models import (
    Battle,
    BattlePet,
    PetMove,
    StatusEffect,
    PetType
)


class BattleSystem:
    """Handles pet battle mechanics and state."""

    @staticmethod
    def calculate_damage(
        move: PetMove,
        attacker: BattlePet,
        defender: BattlePet
    ) -> Tuple[int, str]:
        """Calculate damage for a move, considering elements and status."""
        # Base damage calculation
        damage = move.damage + attacker.pet.base_damage
        
        # Element effectiveness multipliers
        multiplier = 1.0
        
        # Check super effective combinations
        super_effective = (
            (attacker.element == PetType.FIRE and 
             defender.element == PetType.EARTH) or
            (attacker.element == PetType.WATER and 
             defender.element == PetType.FIRE) or
            (attacker.element == PetType.EARTH and 
             defender.element == PetType.AIR) or
            (attacker.element == PetType.AIR and 
             defender.element == PetType.WATER) or
            (attacker.element == PetType.LIGHT and 
             defender.element == PetType.DARK) or
            (attacker.element == PetType.DARK and 
             defender.element == PetType.LIGHT)
        )
        
        # Check not very effective combinations
        not_effective = (
            (defender.element == PetType.FIRE and 
             attacker.element == PetType.EARTH) or
            (defender.element == PetType.WATER and 
             attacker.element == PetType.FIRE) or
            (defender.element == PetType.EARTH and 
             attacker.element == PetType.AIR) or
            (defender.element == PetType.AIR and 
             attacker.element == PetType.WATER) or
            (defender.element == PetType.LIGHT and 
             attacker.element == PetType.DARK) or
            (defender.element == PetType.DARK and 
             attacker.element == PetType.LIGHT)
        )

        if super_effective:
            multiplier = 1.5
            message = "It's super effective! "
        elif not_effective:
            multiplier = 0.5
            message = "It's not very effective... "
        else:
            message = ""

        # Apply status effect modifiers
        if attacker.status == StatusEffect.BURN:
            damage *= 0.8
        elif attacker.status == StatusEffect.PARALYZE:
            if random.random() < 0.25:
                return 0, "Paralysis prevented the attack!"

        # Calculate final damage
        final_damage = int(damage * multiplier)
        
        # Check for status effect application
        if (move.status_effect != StatusEffect.NONE and 
                random.randint(1, 100) <= move.status_chance):
            defender.status = move.status_effect
            defender.status_turns = random.randint(2, 4)
            message += (
                f"{defender.pet.name} was afflicted with "
                f"{move.status_effect.value}!"
            )

        return final_damage, message

    @staticmethod
    def process_turn(
        battle: Battle,
        move: PetMove,
        attacker: BattlePet,
        defender: BattlePet
    ) -> str:
        """Process a single turn of battle."""
        # Check if attacker can move
        if attacker.status == StatusEffect.SLEEP:
            if random.random() < 0.34:  # 34% chance to wake up
                attacker.status = StatusEffect.NONE
                attacker.status_turns = 0
                message = f"{attacker.pet.name} woke up!\n"
            else:
                return f"{attacker.pet.name} is still sleeping!"

        # Calculate accuracy
        if random.randint(1, 100) > move.accuracy:
            return f"{attacker.pet.name}'s {move.name} missed!"

        # Calculate and apply damage
        damage, effect_message = BattleSystem.calculate_damage(
            move, attacker, defender
        )
        defender.current_hp = max(0, defender.current_hp - damage)
        
        # Build battle message
        message = (
            f"{attacker.pet.name} used {move.name} {move.emoji}\n"
            f"{effect_message}\n"
            f"Dealt {damage} damage to {defender.pet.name}!"
        )

        # Check for battle end
        if defender.current_hp == 0:
            battle.is_finished = True
            battle.winner = attacker
            message += f"\n{defender.pet.name} fainted! "
            message += f"{attacker.pet.name} wins!"

        return message

    @staticmethod
    def apply_status_effects(pet: BattlePet) -> Optional[str]:
        """Apply status effect damage/effects at end of turn."""
        if pet.status == StatusEffect.NONE or pet.status_turns <= 0:
            return None

        message = None
        if pet.status == StatusEffect.BURN:
            damage = max(1, int(pet.max_hp * 0.0625))  # 1/16th max HP
            pet.current_hp = max(0, pet.current_hp - damage)
            message = f"{pet.pet.name} took {damage} burn damage!"
        elif pet.status == StatusEffect.POISON:
            damage = max(1, int(pet.max_hp * 0.125))  # 1/8th max HP
            pet.current_hp = max(0, pet.current_hp - damage)
            message = f"{pet.pet.name} took {damage} poison damage!"

        pet.status_turns -= 1
        if pet.status_turns <= 0:
            old_status = pet.status
            pet.status = StatusEffect.NONE
            message = f"{pet.pet.name} recovered from {old_status.value}!"

        return message

    @staticmethod
    def create_battle(
        pet1: BattlePet,
        pet2: BattlePet,
        battle_id: int
    ) -> Battle:
        """Create a new battle between two pets."""
        return Battle(
            id=battle_id,
            pet1=pet1,
            pet2=pet2,
            current_turn=1,
            is_finished=False
        )
