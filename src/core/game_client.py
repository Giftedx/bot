from dataclasses import dataclass
from typing import Optional, Dict, List, Set, Tuple
import asyncio
from datetime import datetime
import math
import random
from enum import Enum

from src.core.mechanics import (
    CombatStats,
    Equipment,
    CombatFormulas,
    PrayerMultipliers,
    ExperienceTable,
    DropRates,
    CombatStyle,
    AttackType,
    AgilityCourse,
    AGILITY_COURSES,
)

# from src.core.config import Config # Removed Config import
from src.core.config import ConfigManager  # Added ConfigManager import
from src.core.interfaces import GameDisplay
from src.core.database import DatabaseManager


# Add new enums
class QuestStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class MinigameType(Enum):
    PEST_CONTROL = "pest_control"
    BARBARIAN_ASSAULT = "barbarian_assault"
    CASTLE_WARS = "castle_wars"
    NIGHTMARE_ZONE = "nmz"
    FISHING_TRAWLER = "fishing_trawler"
    VOLCANIC_MINE = "volcanic_mine"
    TEMPOROSS = "tempoross"


@dataclass
class PlayerState:
    """Represents the current state of a player with all OSRS systems"""

    # Basic info
    user_id: str
    username: str
    created_at: datetime
    last_action: datetime

    # Combat
    combat_stats: CombatStats
    equipment: Equipment
    combat_style: CombatStyle = CombatStyle.ACCURATE
    attack_type: AttackType = AttackType.SLASH

    # Skills and XP
    skills: Dict[str, int] = None  # Skill levels
    experience: Dict[str, int] = None  # Skill XP
    total_level: int = 0
    total_xp: int = 0

    # Inventory & Bank
    inventory: Dict[str, int] = None  # Item ID -> Count
    bank: Dict[str, int] = None  # Item ID -> Count
    inventory_slots: int = 28
    bank_slots: int = 800

    # Location & Movement
    location: str = "Lumbridge"
    previous_location: str = None
    is_moving: bool = False

    # Status
    is_busy: bool = False
    current_action: Optional[str] = None
    prayer_points: int = 1
    run_energy: float = 100.0
    special_attack: int = 100

    # Active effects
    active_prayers: Set[str] = None
    active_potions: Dict[str, datetime] = None
    status_effects: List[Dict] = None

    # Achievement tracking
    quest_points: int = 0
    achievement_diary_progress: Dict[str, Dict[str, bool]] = None
    unlocked_achievements: Set[str] = None

    # Minigame stats
    slayer_task: Optional[Dict] = None
    last_slayer_task: datetime = None
    minigame_points: Dict[str, int] = None

    # Quest System
    quests: Dict[str, QuestStatus] = None
    quest_stages: Dict[str, int] = None

    # Minigame System
    minigame_scores: Dict[MinigameType, int] = None
    minigame_unlocks: Dict[MinigameType, Set[str]] = None

    # Combat System
    hitpoints: int = 10
    max_hitpoints: int = 10
    combat_target: Optional[str] = None
    auto_retaliate: bool = True
    special_attack_energy: int = 100

    # Slayer System
    slayer_points: int = 0
    slayer_streak: int = 0
    slayer_unlocks: Set[str] = None

    # Farming System
    farming_patches: Dict[str, Dict] = None
    farming_timers: Dict[str, datetime] = None
    farming_tools: Set[str] = None

    # Construction System
    house_location: str = "Rimmington"
    house_rooms: Dict[Tuple[int, int, int], Dict] = None
    house_style: str = "Basic wood"
    construction_materials: Dict[str, int] = None

    def __post_init__(self):
        """Initialize default values for collections"""
        if self.skills is None:
            self.skills = {
                "attack": 1,
                "strength": 1,
                "defence": 1,
                "ranged": 1,
                "magic": 1,
                "prayer": 1,
                "runecraft": 1,
                "construction": 1,
                "hitpoints": 10,
                "agility": 1,
                "herblore": 1,
                "crafting": 1,
                "fletching": 1,
                "slayer": 1,
                "hunter": 1,
                "mining": 1,
                "smithing": 1,
                "fishing": 1,
                "cooking": 1,
                "firemaking": 1,
                "woodcutting": 1,
                "farming": 1,
                "thieving": 1,
            }

        if self.experience is None:
            self.experience = {skill: 0 for skill in self.skills}

        if self.inventory is None:
            self.inventory = {}

        if self.bank is None:
            self.bank = {}

        if self.active_prayers is None:
            self.active_prayers = set()

        if self.active_potions is None:
            self.active_potions = {}

        if self.status_effects is None:
            self.status_effects = []

        if self.achievement_diary_progress is None:
            self.achievement_diary_progress = {
                region: {"easy": False, "medium": False, "hard": False, "elite": False}
                for region in [
                    "ardougne",
                    "desert",
                    "falador",
                    "fremennik",
                    "kandarin",
                    "karamja",
                    "lumbridge",
                    "morytania",
                    "varrock",
                    "wilderness",
                ]
            }

        if self.unlocked_achievements is None:
            self.unlocked_achievements = set()

        if self.minigame_points is None:
            self.minigame_points = {
                "pest_control": 0,
                "barbarian_assault": 0,
                "castle_wars": 0,
                "nmz": 0,
            }

        if self.quests is None:
            self.quests = {
                "Cook's Assistant": QuestStatus.NOT_STARTED,
                "Dragon Slayer": QuestStatus.NOT_STARTED,
                # Add more quests...
            }

        if self.quest_stages is None:
            self.quest_stages = {}

        if self.minigame_scores is None:
            self.minigame_scores = {game: 0 for game in MinigameType}

        if self.minigame_unlocks is None:
            self.minigame_unlocks = {game: set() for game in MinigameType}

        if self.slayer_unlocks is None:
            self.slayer_unlocks = set()

        if self.farming_patches is None:
            self.farming_patches = {
                "Falador_Allotment_1": {"state": "empty"},
                "Falador_Allotment_2": {"state": "empty"},
                # Add more patches...
            }

        if self.farming_timers is None:
            self.farming_timers = {}

        if self.farming_tools is None:
            self.farming_tools = set()

        if self.house_rooms is None:
            self.house_rooms = {
                (0, 0, 0): {"type": "Garden", "rotation": 0}
                # Add more rooms as needed
            }

        if self.construction_materials is None:
            self.construction_materials = {}

    def get_skill_level(self, skill: str) -> int:
        """Get current level including boosts"""
        base_level = self.skills.get(skill, 1)

        # Apply prayer boosts
        prayer_mult = 1.0
        if skill in ("attack", "strength", "defence", "ranged", "magic"):
            for prayer in self.active_prayers:
                if prayer in getattr(PrayerMultipliers, f"{skill.upper()}_PRAYERS", {}):
                    prayer_mult = max(prayer_mult, PrayerMultipliers.ATTACK_PRAYERS[prayer])

        # Apply potion boosts
        potion_boost = 0
        # TODO: Add potion boost logic

        return math.floor(base_level * prayer_mult) + potion_boost

    def add_experience(self, skill: str, amount: float) -> List[str]:
        """
        Add experience to a skill and return list of level up messages
        """
        if skill not in self.skills:
            return []

        messages = []
        old_level = self.skills[skill]
        self.experience[skill] += amount
        new_level = ExperienceTable.xp_to_level(self.experience[skill])

        if new_level > old_level:
            self.skills[skill] = new_level
            messages.append(f"Congratulations! You've advanced {skill} to level {new_level}!")

            # Update total level
            self.total_level = sum(self.skills.values())

        # Update total XP
        self.total_xp = sum(self.experience.values())

        return messages


class GameClient:
    """Main game client that coordinates all OSRS systems"""

    # def __init__(self, config: Config): # Old __init__
    def __init__(self, config_manager: ConfigManager):  # New __init__
        self.config_manager = config_manager  # Storing ConfigManager instance
        self.db = (
            DatabaseManager()
        )  # Assuming DatabaseManager handles its own config or is refactored separately
        self.players: Dict[str, PlayerState] = {}
        self.display_mode = "text"
        self.displays: Dict[str, GameDisplay] = {}

        # Combat system
        self.combat_formulas = CombatFormulas()
        self.drop_rates = DropRates()

        # Load game data
        self.items = {}  # TODO: Load item definitions
        self.npcs = {}  # TODO: Load NPC definitions

    async def register_player(self, user_id: str, username: str) -> PlayerState:
        """Register a new player with default stats"""
        if user_id in self.players:
            return self.players[user_id]

        # Check database first
        saved_data = self.db.get_player(user_id)
        if saved_data:
            player = PlayerState(**saved_data["data"])
            self.players[user_id] = player
            return player

        # Create new player
        now = datetime.now()
        player = PlayerState(
            user_id=user_id,
            username=username,
            created_at=now,
            last_action=now,
            combat_stats=CombatStats(
                attack=1, strength=1, defence=1, ranged=1, magic=1, hitpoints=10, prayer=1
            ),
            equipment=Equipment(),
        )

        # Save to database
        self.db.save_player(user_id, username, player.__dict__)

        self.players[user_id] = player
        return player

    async def set_display_mode(self, user_id: str, mode: str):
        """Set display mode for a player (text/graphical)"""
        if mode not in ("text", "graphical"):
            raise ValueError("Invalid display mode")

        if user_id not in self.displays:
            self.displays[user_id] = GameDisplay()

        self.displays[user_id].mode = mode

    async def process_command(self, user_id: str, command: str, args: List[str]) -> str:
        """Process a game command and return response"""
        if user_id not in self.players:
            return "You must register first with !register"

        player = self.players[user_id]

        if player.is_busy:
            return "You're currently busy with another action"

        # Command processing
        if command == "train":
            skill = args[0].lower()
            return await self.train_skill(player, skill)

        elif command == "equip":
            item = " ".join(args)
            return await self.equip_item(player, item)

        elif command == "stats":
            return self.get_stats(player)

        elif command == "inventory":
            return self.get_inventory(player)

        elif command == "bank":
            return self.get_bank(player)

        elif command == "prayer":
            prayer = " ".join(args)
            return await self.toggle_prayer(player, prayer)

        elif command == "attack":
            target = " ".join(args)
            return await self.attack_target(player, target)

        elif command == "move":
            location = " ".join(args)
            return await self.move_to(player, location)

        elif command == "slayer":
            if len(args) < 1:
                return "Usage: !slayer [master/info/skip]"
            action = args[0].lower()

            if action == "master":
                master = " ".join(args[1:])
                return await self.assign_slayer_task(player, master)
            elif action == "info":
                if not player.slayer_task:
                    return "You don't have a slayer task."
                return (
                    f"Current task: {player.slayer_task['amount']} {player.slayer_task['monster']}"
                )

        elif command == "farm":
            if len(args) < 3:
                return "Usage: !farm [plant/check] [patch] [seed]"
            action = args[0].lower()

            if action == "plant":
                patch = args[1]
                seed = args[2]
                return await self.plant_seed(player, patch, seed)
            elif action == "check":
                await self.check_farming_patches(player)
                return "Checked farming patches."

        elif command == "build":
            if len(args) < 4:
                return "Usage: !build [room] [x] [y] [z]"
            room = args[0]
            try:
                x, y, z = map(int, args[1:4])
                return await self.build_room(player, room, x, y, z)
            except ValueError:
                return "Invalid coordinates."

        return f"Unknown command: {command}"

    async def train_skill(self, player: PlayerState, skill: str) -> str:
        """Handle skill training with proper XP rates"""
        if skill not in player.skills:
            return f"Invalid skill: {skill}"

        player.is_busy = True
        player.current_action = f"Training {skill}"

        try:
            # Get XP rate based on level and method
            base_xp = 40  # Base XP per action
            level_mult = (player.skills[skill] + 1) / 30  # Higher levels = more XP

            # Simulate training
            await asyncio.sleep(3)

            # Add XP and get messages
            messages = player.add_experience(skill, base_xp * level_mult)

            # Save progress
            self.db.save_player(player.user_id, player.username, player.__dict__)

            return "\n".join([f"You gained {base_xp * level_mult:.1f} {skill} XP.", *messages])

        finally:
            player.is_busy = False
            player.current_action = None

    async def equip_item(self, player: PlayerState, item: str) -> str:
        """Handle equipment changes"""
        # Equipment logic here
        return f"Equipped {item}"

    async def toggle_prayer(self, player: PlayerState, prayer: str) -> str:
        """Toggle a prayer on/off"""
        prayer = prayer.title()

        # Check if valid prayer
        valid_prayers = set()
        for prayer_list in (
            PrayerMultipliers.ATTACK_PRAYERS,
            PrayerMultipliers.STRENGTH_PRAYERS,
            PrayerMultipliers.DEFENCE_PRAYERS,
            PrayerMultipliers.RANGED_PRAYERS,
            PrayerMultipliers.MAGIC_PRAYERS,
        ):
            valid_prayers.update(prayer_list.keys())

        if prayer not in valid_prayers:
            return f"Invalid prayer: {prayer}"

        # Toggle prayer
        if prayer in player.active_prayers:
            player.active_prayers.remove(prayer)
            return f"Deactivated {prayer} prayer"
        else:
            player.active_prayers.add(prayer)
            return f"Activated {prayer} prayer"

    async def attack_target(self, player: PlayerState, target: str) -> str:
        """Handle combat with NPCs"""
        if player.is_busy:
            return "You're already in combat!"

        npc = self.npcs.get(target)
        if not npc:
            return f"Could not find {target}"

        player.is_busy = True
        player.combat_target = target

        # Start combat loop
        asyncio.create_task(self._combat_loop(player, npc))

        return f"You begin attacking {target}!"

    async def _combat_loop(self, player: PlayerState, npc: Dict):
        """Handle combat calculations and updates"""
        try:
            while player.combat_target and player.hitpoints > 0:
                # Calculate damage
                max_hit = self.combat_formulas.calculate_max_hit(
                    player.get_skill_level("strength"),
                    player.get_skill_level("attack"),
                    player.equipment.melee_strength,
                )

                hit = random.randint(0, max_hit)

                # Apply damage
                npc_hp = npc.get("hitpoints", 0) - hit

                if hit > 0:
                    await self.send_message(player, f"You hit {hit} damage!")
                else:
                    await self.send_message(player, "You miss!")

                if npc_hp <= 0:
                    # Handle kill
                    await self._handle_kill(player, npc)
                    break

                # NPC attacks back
                npc_max_hit = npc.get("max_hit", 1)
                npc_hit = random.randint(0, npc_max_hit)

                player.hitpoints -= npc_hit
                if npc_hit > 0:
                    await self.send_message(player, f"{target} hits you for {npc_hit} damage!")

                if player.hitpoints <= 0:
                    await self._handle_death(player)
                    break

                await asyncio.sleep(2.4)  # Standard attack speed

        finally:
            player.is_busy = False
            player.combat_target = None

    async def _handle_kill(self, player: PlayerState, npc: Dict):
        """Handle NPC death and drops"""
        # Calculate drops
        drops = []
        for item, chance in npc.get("drops", {}).items():
            if random.random() < self.drop_rates.calculate_drop_chance(chance):
                drops.append(item)

        # Add drops to inventory
        for item in drops:
            if len(player.inventory) < player.inventory_slots:
                player.inventory[item] = player.inventory.get(item, 0) + 1
                await self.send_message(player, f"You receive: {item}")

        # Handle slayer task
        if player.slayer_task and npc["name"] == player.slayer_task["monster"]:
            player.slayer_task["amount"] -= 1
            if player.slayer_task["amount"] <= 0:
                await self._complete_slayer_task(player)

    async def _handle_death(self, player: PlayerState):
        """Handle player death"""
        await self.send_message(player, "Oh dear, you are dead!")

        # Reset stats
        player.hitpoints = player.max_hitpoints

        # Move to respawn point
        player.location = "Lumbridge"

        # Drop items if needed
        # TODO: Implement item loss on death

    async def assign_slayer_task(self, player: PlayerState, master: str) -> str:
        """Assign a new slayer task"""
        if player.slayer_task:
            return "You already have a slayer task!"

        # Get task list for master
        tasks = self.slayer_tasks.get(master, [])
        if not tasks:
            return f"Invalid slayer master: {master}"

        # Assign random task
        task = random.choice(tasks)
        player.slayer_task = {
            "monster": task["monster"],
            "amount": random.randint(task["min"], task["max"]),
            "master": master,
        }

        return f"Your new task is to kill {player.slayer_task['amount']} {player.slayer_task['monster']}."

    async def plant_seed(self, player: PlayerState, patch: str, seed: str) -> str:
        """Plant a seed in a farming patch"""
        if patch not in player.farming_patches:
            return f"Invalid patch: {patch}"

        patch_data = player.farming_patches[patch]
        if patch_data["state"] != "empty":
            return "This patch is not empty!"

        # Check seed requirements
        seed_data = self.seeds.get(seed)
        if not seed_data:
            return f"Invalid seed: {seed}"

        if player.get_skill_level("farming") < seed_data["level"]:
            return f"You need level {seed_data['level']} Farming to plant this seed."

        # Plant seed
        patch_data.update(
            {
                "state": "growing",
                "seed": seed,
                "stage": 0,
                "planted_at": datetime.now(),
                "water_level": 0,
                "disease": False,
            }
        )

        player.farming_timers[patch] = datetime.now()

        return f"You plant the {seed}."

    async def check_farming_patches(self, player: PlayerState):
        """Update farming patch states"""
        now = datetime.now()
        for patch, timer in player.farming_timers.items():
            patch_data = player.farming_patches[patch]
            if patch_data["state"] != "growing":
                continue

            seed_data = self.seeds[patch_data["seed"]]

            # Check growth
            stages = seed_data["stages"]
            stage_time = seed_data["minutes_per_stage"]

            elapsed = (now - timer).total_seconds() / 60
            new_stage = min(stages, int(elapsed / stage_time))

            if new_stage > patch_data["stage"]:
                patch_data["stage"] = new_stage
                if new_stage >= stages:
                    patch_data["state"] = "ready"
                    await self.send_message(
                        player, f"Your {patch_data['seed']} is ready to harvest!"
                    )

    async def build_room(self, player: PlayerState, room_type: str, x: int, y: int, z: int) -> str:
        """Build a new room in player's house"""
        coords = (x, y, z)

        # Check if space is available
        if coords in player.house_rooms:
            return "There is already a room here!"

        # Check requirements
        room_data = self.construction_rooms.get(room_type)
        if not room_data:
            return f"Invalid room type: {room_type}"

        if player.get_skill_level("construction") < room_data["level"]:
            return f"You need level {room_data['level']} Construction to build this room."

        # Check materials
        for material, amount in room_data["materials"].items():
            if player.construction_materials.get(material, 0) < amount:
                return f"You need {amount} {material} to build this room."

        # Build room
        for material, amount in room_data["materials"].items():
            player.construction_materials[material] -= amount

        player.house_rooms[coords] = {"type": room_type, "rotation": 0, "furniture": {}}

        # Add XP
        messages = player.add_experience("construction", room_data["xp"])

        return "\n".join([f"You build a {room_type}!", *messages])

    async def update_display(self, user_id: str):
        """Update the player's game display"""
        if user_id not in self.displays:
            return

        display = self.displays[user_id]
        player = self.players[user_id]

        if display.mode == "text":
            # Update text display
            display.update_text(self.get_stats(player))
        else:
            # Update graphical display
            display.update_graphics(player)
