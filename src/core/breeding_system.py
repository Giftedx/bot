from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from datetime import datetime, timedelta
import random
import uuid

from .pet_system import Pet, PetRarity, PetAbility
from ..features.pets.event_system import EventManager, EventType, GameEvent


class BreedingCompatibility(Enum):
    INCOMPATIBLE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    PERFECT = 4


class BreedingState(Enum):
    READY = "ready"
    BREEDING = "breeding"
    COOLDOWN = "cooldown"


class BreedingResult:
    def __init__(
        self,
        success: bool,
        parent1: Pet,
        parent2: Pet,
        offspring: Optional[Pet] = None,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.success = success
        self.parent1 = parent1
        self.parent2 = parent2
        self.offspring = offspring
        self.message = message
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()


class BreedingPair:
    def __init__(self, pet1: Pet, pet2: Pet):
        self.pet1 = pet1
        self.pet2 = pet2
        self.state = BreedingState.READY
        self.start_time: Optional[datetime] = None
        self.completion_time: Optional[datetime] = None
        self.breeding_duration: Optional[timedelta] = None

    def start_breeding(self, duration_hours: int) -> None:
        """Start the breeding process"""
        self.state = BreedingState.BREEDING
        self.start_time = datetime.utcnow()
        self.breeding_duration = timedelta(hours=duration_hours)
        self.completion_time = self.start_time + self.breeding_duration

    def is_complete(self) -> bool:
        """Check if breeding is complete"""
        if self.state != BreedingState.BREEDING or not self.completion_time:
            return False
        return datetime.utcnow() >= self.completion_time


class BreedingSystem:
    def __init__(self, event_manager: Optional[EventManager] = None):
        self.event_manager = event_manager
        self.active_pairs: Dict[str, BreedingPair] = {}
        self.breeding_history: List[BreedingResult] = []
        self.cooldown_periods: Dict[str, datetime] = {}  # pet_id -> cooldown end time

        # Breeding configuration
        self.config = {
            "min_level": 10,
            "base_duration_hours": 24,
            "cooldown_hours": 72,
            "success_rates": {
                BreedingCompatibility.INCOMPATIBLE: 0.0,
                BreedingCompatibility.LOW: 0.3,
                BreedingCompatibility.MEDIUM: 0.5,
                BreedingCompatibility.HIGH: 0.7,
                BreedingCompatibility.PERFECT: 0.9,
            },
            "rarity_inheritance": {
                "same": 0.6,  # 60% chance to inherit same rarity
                "higher": 0.1,  # 10% chance for higher rarity
                "lower": 0.3,  # 30% chance for lower rarity
            },
        }

    def check_compatibility(self, pet1: Pet, pet2: Pet) -> BreedingCompatibility:
        """Check breeding compatibility between two pets"""
        # Same pet can't breed
        if pet1.pet_id == pet2.pet_id:
            return BreedingCompatibility.INCOMPATIBLE

        # Check origins
        if pet1.origin != pet2.origin:
            return BreedingCompatibility.LOW

        # Check levels
        if (
            pet1.stats.level < self.config["min_level"]
            or pet2.stats.level < self.config["min_level"]
        ):
            return BreedingCompatibility.INCOMPATIBLE

        # Calculate compatibility score
        score = 0

        # Rarity compatibility
        if pet1.rarity == pet2.rarity:
            score += 2
        elif abs(pet1.rarity.value - pet2.rarity.value) == 1:
            score += 1

        # Level compatibility
        level_diff = abs(pet1.stats.level - pet2.stats.level)
        if level_diff <= 5:
            score += 2
        elif level_diff <= 10:
            score += 1

        # Loyalty bonus
        if pet1.stats.loyalty >= 50 and pet2.stats.loyalty >= 50:
            score += 1

        # Map score to compatibility
        if score >= 5:
            return BreedingCompatibility.PERFECT
        elif score >= 4:
            return BreedingCompatibility.HIGH
        elif score >= 2:
            return BreedingCompatibility.MEDIUM
        else:
            return BreedingCompatibility.LOW

    def can_breed(self, pet1: Pet, pet2: Pet) -> Tuple[bool, str]:
        """Check if two pets can breed"""
        # Check cooldowns
        now = datetime.utcnow()
        for pet in [pet1, pet2]:
            if pet.pet_id in self.cooldown_periods:
                if now < self.cooldown_periods[pet.pet_id]:
                    return False, f"{pet.name} is still in breeding cooldown"

        # Check if either pet is already breeding
        for pair in self.active_pairs.values():
            if pet1.pet_id in [pair.pet1.pet_id, pair.pet2.pet_id] or pet2.pet_id in [
                pair.pet1.pet_id,
                pair.pet2.pet_id,
            ]:
                return False, "One or both pets are already breeding"

        # Check compatibility
        compatibility = self.check_compatibility(pet1, pet2)
        if compatibility == BreedingCompatibility.INCOMPATIBLE:
            return False, "Pets are not compatible for breeding"

        return True, "Pets can breed"

    def start_breeding(self, pet1: Pet, pet2: Pet) -> BreedingResult:
        """Start breeding two pets"""
        can_breed, message = self.can_breed(pet1, pet2)
        if not can_breed:
            return BreedingResult(False, pet1, pet2, message=message)

        # Create breeding pair
        pair_id = str(uuid.uuid4())
        pair = BreedingPair(pet1, pet2)

        # Calculate breeding duration based on rarity and compatibility
        compatibility = self.check_compatibility(pet1, pet2)
        duration_modifier = 1.0
        if compatibility == BreedingCompatibility.PERFECT:
            duration_modifier = 0.7
        elif compatibility == BreedingCompatibility.HIGH:
            duration_modifier = 0.85
        elif compatibility == BreedingCompatibility.LOW:
            duration_modifier = 1.3

        duration_hours = int(self.config["base_duration_hours"] * duration_modifier)
        pair.start_breeding(duration_hours)

        self.active_pairs[pair_id] = pair

        # Emit breeding started event
        if self.event_manager:
            self.event_manager.emit(
                GameEvent(
                    type=EventType.BREEDING_STARTED,
                    user_id=str(pet1.owner_id),
                    timestamp=datetime.utcnow(),
                    data={
                        "pair_id": pair_id,
                        "pet1_id": pet1.pet_id,
                        "pet2_id": pet2.pet_id,
                        "duration_hours": duration_hours,
                        "completion_time": pair.completion_time.isoformat(),
                    },
                )
            )

        return BreedingResult(
            True,
            pet1,
            pet2,
            message=f"Breeding started, will complete in {duration_hours} hours",
            metadata={"pair_id": pair_id, "completion_time": pair.completion_time},
        )

    def check_breeding_progress(self, pair_id: str) -> Optional[BreedingResult]:
        """Check progress of a breeding pair"""
        pair = self.active_pairs.get(pair_id)
        if not pair:
            return None

        if not pair.is_complete():
            time_remaining = pair.completion_time - datetime.utcnow()
            return BreedingResult(
                False,
                pair.pet1,
                pair.pet2,
                message=f"Breeding in progress, {time_remaining.total_seconds() / 3600:.1f} hours remaining",
                metadata={"time_remaining": time_remaining.total_seconds()},
            )

        # Breeding is complete, generate offspring
        offspring = self._generate_offspring(pair)

        # Set cooldown periods for parents
        cooldown_end = datetime.utcnow() + timedelta(hours=self.config["cooldown_hours"])
        self.cooldown_periods[pair.pet1.pet_id] = cooldown_end
        self.cooldown_periods[pair.pet2.pet_id] = cooldown_end

        # Remove breeding pair
        del self.active_pairs[pair_id]

        result = BreedingResult(
            True,
            pair.pet1,
            pair.pet2,
            offspring,
            message="Breeding complete!",
            metadata={"cooldown_end": cooldown_end},
        )

        self.breeding_history.append(result)

        # Emit breeding completed event
        if self.event_manager:
            self.event_manager.emit(
                GameEvent(
                    type=EventType.BREEDING_COMPLETED,
                    user_id=str(pair.pet1.owner_id),
                    timestamp=datetime.utcnow(),
                    data={
                        "pair_id": pair_id,
                        "pet1_id": pair.pet1.pet_id,
                        "pet2_id": pair.pet2.pet_id,
                        "offspring_id": offspring.pet_id,
                        "offspring_rarity": offspring.rarity.value,
                    },
                )
            )

        return result

    def _generate_offspring(self, pair: BreedingPair) -> Pet:
        """Generate offspring from a breeding pair"""
        # Determine rarity
        rarity = self._determine_offspring_rarity(pair.pet1, pair.pet2)

        # Generate base stats
        base_stats = self._inherit_stats(pair.pet1, pair.pet2)

        # Inherit abilities
        abilities = self._inherit_abilities(pair.pet1, pair.pet2)

        # Create offspring
        offspring = Pet(
            pet_id=str(uuid.uuid4()),
            name=f"Offspring of {pair.pet1.name} & {pair.pet2.name}",
            origin=pair.pet1.origin,  # Inherit origin from first parent
            rarity=rarity,
            owner_id=pair.pet1.owner_id,  # Assign to first parent's owner
            base_stats=base_stats,
            abilities=abilities,
        )

        # Add some random variation to stats
        for stat in offspring.stats.skill_levels:
            variation = random.uniform(-0.1, 0.1)  # ±10% variation
            current = offspring.stats.skill_levels[stat]
            offspring.stats.skill_levels[stat] = max(1, int(current * (1 + variation)))

        return offspring

    def _determine_offspring_rarity(self, pet1: Pet, pet2: Pet) -> PetRarity:
        """Determine offspring's rarity based on parents"""
        roll = random.random()

        if pet1.rarity == pet2.rarity:
            # Same rarity parents
            if roll < self.config["rarity_inheritance"]["same"]:
                return pet1.rarity
            elif (
                roll
                < self.config["rarity_inheritance"]["same"]
                + self.config["rarity_inheritance"]["higher"]
            ):
                # Try to go up one rarity level
                rarity_values = list(PetRarity)
                current_index = rarity_values.index(pet1.rarity)
                if current_index < len(rarity_values) - 1:
                    return rarity_values[current_index + 1]
                return pet1.rarity
            else:
                # Go down one rarity level
                rarity_values = list(PetRarity)
                current_index = rarity_values.index(pet1.rarity)
                if current_index > 0:
                    return rarity_values[current_index - 1]
                return pet1.rarity
        else:
            # Different rarity parents
            if roll < 0.5:
                return pet1.rarity
            else:
                return pet2.rarity

    def _inherit_stats(self, pet1: Pet, pet2: Pet) -> Dict[str, int]:
        """Generate inherited base stats"""
        inherited_stats = {}
        for stat in pet1.base_stats:
            # 40-60% from each parent
            pet1_contribution = random.uniform(0.4, 0.6)
            pet2_contribution = 1 - pet1_contribution

            inherited_value = int(
                pet1.base_stats[stat] * pet1_contribution
                + pet2.base_stats[stat] * pet2_contribution
            )
            inherited_stats[stat] = max(1, inherited_value)

        return inherited_stats

    def _inherit_abilities(self, pet1: Pet, pet2: Pet) -> List[PetAbility]:
        """Inherit abilities from parents"""
        # Pool all abilities from both parents
        all_abilities = pet1.abilities + pet2.abilities

        # Remove duplicates
        unique_abilities = list({ability.name: ability for ability in all_abilities}.values())

        # Randomly select abilities to inherit (50% chance for each)
        inherited = []
        for ability in unique_abilities:
            if random.random() < 0.5:
                inherited.append(ability)

        # Ensure at least one ability is inherited
        if not inherited and unique_abilities:
            inherited.append(random.choice(unique_abilities))

        return inherited

    def get_breeding_history(
        self, pet_id: Optional[str] = None, limit: int = 10
    ) -> List[BreedingResult]:
        """Get breeding history with optional filtering"""
        history = self.breeding_history
        if pet_id:
            history = [
                result
                for result in history
                if pet_id in [result.parent1.pet_id, result.parent2.pet_id]
            ]
        return sorted(history, key=lambda r: r.timestamp, reverse=True)[:limit]

    def get_active_breedings(self, pet_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all active breeding pairs"""
        active = []
        for pair_id, pair in self.active_pairs.items():
            if pet_id and pet_id not in [pair.pet1.pet_id, pair.pet2.pet_id]:
                continue

            time_remaining = None
            if pair.completion_time:
                time_remaining = (pair.completion_time - datetime.utcnow()).total_seconds()

            active.append(
                {
                    "pair_id": pair_id,
                    "pet1_id": pair.pet1.pet_id,
                    "pet2_id": pair.pet2.pet_id,
                    "state": pair.state.value,
                    "start_time": pair.start_time.isoformat() if pair.start_time else None,
                    "completion_time": pair.completion_time.isoformat()
                    if pair.completion_time
                    else None,
                    "time_remaining_seconds": time_remaining,
                }
            )

        return active

    def get_cooldown_status(self, pet_id: str) -> Optional[Dict[str, Any]]:
        """Get breeding cooldown status for a pet"""
        if pet_id not in self.cooldown_periods:
            return None

        cooldown_end = self.cooldown_periods[pet_id]
        now = datetime.utcnow()

        if now >= cooldown_end:
            del self.cooldown_periods[pet_id]
            return None

        time_remaining = (cooldown_end - now).total_seconds()
        return {"cooldown_end": cooldown_end.isoformat(), "time_remaining_seconds": time_remaining}
