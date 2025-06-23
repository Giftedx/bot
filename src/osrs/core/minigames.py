"""OSRS minigames implementation."""
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import random
from datetime import datetime

from .game_math import calculate_hit_chance, calculate_max_hit


class MinigameType(Enum):
    """Available minigames."""

    WARRIORS_GUILD = "warriors_guild"
    PEST_CONTROL = "pest_control"
    BARBARIAN_ASSAULT = "barbarian_assault"
    CASTLE_WARS = "castle_wars"
    FIGHT_CAVES = "fight_caves"
    INFERNO = "inferno"
    NIGHTMARE_ZONE = "nightmare_zone"
    TEMPOROSS = "tempoross"
    VOLCANIC_MINE = "volcanic_mine"
    GAUNTLET = "gauntlet"
    ZALCANO = "zalcano"
    SOUL_WARS = "soul_wars"
    MAHOGANY_HOMES = "mahogany_homes"
    HALLOWED_SEPULCHRE = "hallowed_sepulchre"
    FISHING_TRAWLER = "fishing_trawler"
    TROUBLE_BREWING = "trouble_brewing"
    PYRAMID_PLUNDER = "pyramid_plunder"


@dataclass
class MinigameRewards:
    """Rewards for completing a minigame."""

    xp: Dict[str, int]
    items: List[Dict[str, int]]  # List of {item_id: quantity}
    points: int = 0
    tokens: int = 0


@dataclass
class Enemy:
    """Represents an enemy in combat minigames."""

    name: str
    level: int
    hp: int
    max_hit: int
    attack_style: str
    weakness: str = None
    special_attacks: List[str] = None


class MinigameManager:
    """Manages OSRS minigames."""

    def __init__(self):
        self.active_sessions: Dict[int, Dict] = {}

        # Minigame requirements
        self.requirements = {
            MinigameType.WARRIORS_GUILD: {
                "skills": {"attack": 65, "strength": 65},
                "items": ["dragon_defender"],
                "quests": [],
            },
            MinigameType.PEST_CONTROL: {"combat_level": 40, "items": [], "quests": []},
            MinigameType.BARBARIAN_ASSAULT: {
                "skills": {},
                "items": [],
                "quests": ["barbarian_training"],
            },
            MinigameType.CASTLE_WARS: {"combat_level": 3, "items": [], "quests": []},
            MinigameType.FIGHT_CAVES: {"combat_level": 70, "items": ["range_weapon"], "quests": []},
            MinigameType.INFERNO: {"combat_level": 100, "items": ["fire_cape"], "quests": []},
            MinigameType.NIGHTMARE_ZONE: {
                "quests": ["five_quests"],  # Need 5 quest bosses
                "combat_level": 40,
            },
            MinigameType.TEMPOROSS: {"skills": {"fishing": 35}},
            MinigameType.VOLCANIC_MINE: {"skills": {"mining": 50}},
            MinigameType.GAUNTLET: {"quests": ["song_of_the_elves"]},
            MinigameType.ZALCANO: {
                "skills": {"mining": 70, "smithing": 70, "runecraft": 70},
                "quests": ["song_of_the_elves"],
            },
            MinigameType.SOUL_WARS: {"combat_level": 40, "quests": []},
            MinigameType.MAHOGANY_HOMES: {
                "skills": {"construction": 20},
                "items": ["hammer", "saw"],
            },
            MinigameType.HALLOWED_SEPULCHRE: {
                "skills": {"agility": 52},
                "quests": ["sins_of_the_father"],
            },
            MinigameType.FISHING_TRAWLER: {
                "skills": {"fishing": 15},
                "items": ["bailing_bucket"],
                "quests": [],
            },
            MinigameType.TROUBLE_BREWING: {"skills": {"cooking": 40}, "quests": ["cabin_fever"]},
            MinigameType.PYRAMID_PLUNDER: {
                "skills": {"thieving": 21},
                "quests": ["icthlarins_little_helper"],
            },
        }

        # Minigame rewards
        self.rewards = {
            MinigameType.WARRIORS_GUILD: {
                "tokens": (50, 100),
                "xp": {"attack": 500, "strength": 500, "defence": 500},
                "items": [{"id": "dragon_defender", "chance": 0.1}],
            },
            MinigameType.PEST_CONTROL: {
                "points": (2, 4),
                "xp": {"choice": 3000},  # Player can choose skill
                "items": [{"id": "void_equipment", "cost": 100}],
            },
            MinigameType.FIGHT_CAVES: {
                "items": [{"id": "fire_cape", "chance": 1.0}],
                "xp": {
                    "attack": 16064,
                    "strength": 16064,
                    "defence": 16064,
                    "ranged": 16064,
                    "magic": 16064,
                    "hitpoints": 32128,
                },
            },
            MinigameType.INFERNO: {
                "items": [{"id": "infernal_cape", "chance": 1.0}],
                "xp": {
                    "attack": 32128,
                    "strength": 32128,
                    "defence": 32128,
                    "ranged": 32128,
                    "magic": 32128,
                    "hitpoints": 64256,
                },
            },
            MinigameType.NIGHTMARE_ZONE: {
                "points": (200000, 300000),
                "xp": {"choice": 80000},  # Per hour
            },
            MinigameType.TEMPOROSS: {
                "xp": {"fishing": 50000},  # Per hour
                "items": [
                    {"id": "fish_barrel", "chance": 0.01},
                    {"id": "tackle_box", "chance": 0.01},
                    {"id": "spirit_angler_outfit", "chance": 0.02},
                ],
            },
            MinigameType.ZALCANO: {
                "xp": {"mining": 25000, "smithing": 25000, "runecraft": 25000},
                "items": [
                    {"id": "crystal_tool_seed", "chance": 0.01},
                    {"id": "zalcano_shard", "chance": 0.1},
                    {"id": "crystal_shard", "chance": 0.5},
                ],
            },
            MinigameType.SOUL_WARS: {
                "points": (20, 50),  # Zeal points
                "xp": {"choice": 40000},  # Per game
                "items": [
                    {"id": "soul_cape", "cost": 1000},
                    {"id": "ectoplasmator", "cost": 500},
                    {"id": "spoils_of_war", "cost": 100},
                ],
            },
            MinigameType.MAHOGANY_HOMES: {
                "points": (2, 6),  # Carpenter points
                "xp": {"construction": 25000},  # Per hour
                "items": [
                    {"id": "builders_supply_crate", "cost": 25},
                    {"id": "amy_saw", "cost": 500},
                    {"id": "plank_sack", "cost": 350},
                ],
            },
            MinigameType.HALLOWED_SEPULCHRE: {
                "points": (100, 200),  # Hallowed marks
                "xp": {"agility": 60000},  # Per hour
                "items": [
                    {"id": "dark_dye", "cost": 300},
                    {"id": "dark_graceful", "cost": 3000},
                    {"id": "ring_of_endurance", "chance": 0.001},
                    {"id": "strange_old_lockpick", "chance": 0.01},
                ],
            },
            MinigameType.FISHING_TRAWLER: {
                "xp": {"fishing": 30000},  # Per hour
                "items": [
                    {"id": "angler_outfit", "chance": 0.02},
                    {"id": "raw_fish", "chance": 1.0},
                ],
            },
            MinigameType.TROUBLE_BREWING: {
                "points": (5, 15),  # Pieces of Eight
                "xp": {"cooking": 25000},  # Per hour
                "items": [
                    {"id": "naval_outfit", "cost": 100},
                    {"id": "the_stuff", "cost": 5},
                    {"id": "rum_recipe", "cost": 250},
                ],
            },
            MinigameType.PYRAMID_PLUNDER: {
                "xp": {"thieving": 45000},  # Per hour
                "items": [
                    {"id": "pharaohs_sceptre", "chance": 0.001},
                    {"id": "golden_scarab", "chance": 0.02},
                    {"id": "golden_idol", "chance": 0.02},
                    {"id": "golden_statuette", "chance": 0.02},
                    {"id": "jewelled_golden_statuette", "chance": 0.02},
                ],
            },
        }

        # Add Fight Caves waves
        self.fight_caves_waves = {
            1: [Enemy("TzKet", 22, 10, 4, "melee")],
            2: [Enemy("TzKet", 22, 10, 4, "melee"), Enemy("TzKet", 22, 10, 4, "melee")],
            3: [Enemy("TzKih", 30, 15, 7, "ranged")],
            # ... more waves ...
            63: [
                Enemy(
                    "TzTok-Jad", 702, 255, 97, "all", special_attacks=["ranged", "magic", "melee"]
                )
            ],
        }

        # Add Inferno waves
        self.inferno_waves = {
            1: [Enemy("Nibbler", 32, 10, 4, "melee")],
            2: [Enemy("Jal-MejRah", 85, 25, 15, "magic")],
            # ... more waves ...
            69: [
                Enemy(
                    "TzKal-Zuk",
                    1400,
                    600,
                    251,
                    "all",
                    special_attacks=["shield", "rangers", "mage"],
                )
            ],
        }

    async def start_minigame(
        self, minigame: MinigameType, player_id: int, player_stats: Dict
    ) -> Optional[str]:
        """
        Start a minigame session.

        Args:
            minigame: Type of minigame
            player_id: Player's ID
            player_stats: Player's current stats

        Returns:
            Optional[str]: Error message if failed, None if successful
        """
        # Check requirements
        if error := self._check_requirements(minigame, player_stats):
            return error

        # Initialize session
        session = {
            "type": minigame,
            "player_id": player_id,
            "start_time": datetime.now(),
            "progress": 0,
            "points": 0,
            "waves_completed": 0,
        }

        self.active_sessions[player_id] = session
        return None

    def _check_requirements(self, minigame: MinigameType, player_stats: Dict) -> Optional[str]:
        """Check if player meets minigame requirements."""
        reqs = self.requirements[minigame]

        # Check combat level
        if "combat_level" in reqs:
            if player_stats["combat_level"] < reqs["combat_level"]:
                return f"Requires combat level {reqs['combat_level']}"

        # Check skill levels
        if "skills" in reqs:
            for skill, level in reqs["skills"].items():
                if player_stats["skills"][skill] < level:
                    return f"Requires {skill} level {level}"

        # Check items (simplified)
        if "items" in reqs and reqs["items"]:
            return "Missing required items"  # Would check inventory

        return None

    async def process_minigame_tick(self, player_id: int, action: Optional[str] = None) -> Dict:
        """Process one tick of minigame gameplay."""
        if player_id not in self.active_sessions:
            return {"error": "No active session"}

        session = self.active_sessions[player_id]

        if session["type"] == MinigameType.WARRIORS_GUILD:
            return self._process_warriors_guild(session, action)
        elif session["type"] == MinigameType.PEST_CONTROL:
            return self._process_pest_control(session, action)
        elif session["type"] == MinigameType.BARBARIAN_ASSAULT:
            return self._process_barbarian_assault(session, action)
        elif session["type"] == MinigameType.CASTLE_WARS:
            return self._process_castle_wars(session, action)
        elif session["type"] == MinigameType.FIGHT_CAVES:
            return await self._process_fight_caves(session, action)
        elif session["type"] == MinigameType.INFERNO:
            return await self._process_inferno(session, action)
        elif session["type"] == MinigameType.NIGHTMARE_ZONE:
            return self._process_nightmare_zone(session, action)
        elif session["type"] == MinigameType.TEMPOROSS:
            return self._process_tempoross(session, action)
        elif session["type"] == MinigameType.VOLCANIC_MINE:
            return self._process_volcanic_mine(session, action)
        elif session["type"] == MinigameType.GAUNTLET:
            return self._process_gauntlet(session, action)
        elif session["type"] == MinigameType.ZALCANO:
            return self._process_zalcano(session, action)
        elif session["type"] == MinigameType.SOUL_WARS:
            return self._process_soul_wars(session, action)
        elif session["type"] == MinigameType.MAHOGANY_HOMES:
            return self._process_mahogany_homes(session, action)
        elif session["type"] == MinigameType.HALLOWED_SEPULCHRE:
            return self._process_hallowed_sepulchre(session, action)
        elif session["type"] == MinigameType.FISHING_TRAWLER:
            return self._process_fishing_trawler(session, action)
        elif session["type"] == MinigameType.TROUBLE_BREWING:
            return self._process_trouble_brewing(session, action)
        elif session["type"] == MinigameType.PYRAMID_PLUNDER:
            return self._process_pyramid_plunder(session, action)

        return {"error": "Unknown minigame type"}

    def _process_warriors_guild(self, session: Dict, action: Optional[str]) -> Dict:
        """Process Warriors Guild gameplay."""
        # Simplified example
        if random.random() < 0.2:  # 20% chance per tick
            session["points"] += random.randint(1, 3)
            return {
                "message": "Successfully defended against cyclops!",
                "points": session["points"],
            }
        return {"message": "Continuing to fight...", "points": session["points"]}

    def _process_pest_control(self, session: Dict, action: Optional[str]) -> Dict:
        """Process Pest Control gameplay."""
        # Simplified example
        if session["progress"] < 100:
            session["progress"] += random.randint(5, 15)
            return {
                "message": f'Defending portals... ({session["progress"]}%)',
                "progress": session["progress"],
            }
        else:
            reward = self._calculate_rewards(MinigameType.PEST_CONTROL, session)
            self._end_session(session["player_id"])
            return {"message": "Game completed!", "rewards": reward}

    def _process_barbarian_assault(self, session: Dict, action: str) -> Dict:
        """Process Barbarian Assault gameplay."""
        role = session.get("role", "attacker")
        wave = session.get("wave", 1)
        points = session.get("points", 0)

        if action == "call":
            # Call out correct attack style/poison/food/etc.
            call = random.choice(["red", "green", "blue"])
            session["current_call"] = call
            return {"message": f"Called out {call}!", "call": call}

        elif action == "attack":
            if role != "attacker":
                return {"error": "You are not an attacker!"}

            # Check if using correct attack style
            if not session.get("current_call"):
                return {"error": "You need to call out the attack style first!"}

            success = random.random() < 0.7  # 70% success rate
            if success:
                session["points"] += 4
                return {"message": "Successfully attacked!", "points": session["points"]}
            return {"message": "Missed the attack!"}

        elif action == "heal":
            if role != "healer":
                return {"error": "You are not a healer!"}

            # Heal teammates
            heal_amount = random.randint(5, 15)
            session["team_hp"] = min(99, session["team_hp"] + heal_amount)
            session["points"] += 2

            return {
                "message": f"Healed team for {heal_amount} HP!",
                "team_hp": session["team_hp"],
                "points": session["points"],
            }

        elif action == "collect":
            if role != "collector":
                return {"error": "You are not a collector!"}

            # Collect eggs
            eggs_collected = random.randint(1, 3)
            session["eggs"] = session.get("eggs", 0) + eggs_collected
            session["points"] += eggs_collected

            return {
                "message": f"Collected {eggs_collected} eggs!",
                "total_eggs": session["eggs"],
                "points": session["points"],
            }

        elif action == "defend":
            if role != "defender":
                return {"error": "You are not a defender!"}

            # Repair barricades and lure runners
            success = random.random() < 0.8  # 80% success rate
            if success:
                session["points"] += 3
                return {"message": "Successfully defended!", "points": session["points"]}
            return {"message": "Failed to defend!"}

        elif action == "change_role":
            # Rotate roles between waves
            roles = ["attacker", "defender", "collector", "healer"]
            current_index = roles.index(role)
            new_role = roles[(current_index + 1) % 4]
            session["role"] = new_role

            return {"message": f"Changed role to {new_role}!", "role": new_role}

        return {"message": "Invalid action"}

    def _process_castle_wars(self, session: Dict, action: str) -> Dict:
        """Process Castle Wars gameplay."""
        team = session.get("team", "saradomin")
        score = session.get("score", {"saradomin": 0, "zamorak": 0})

        if action == "attack":
            # Combat with other players
            hit = random.random() < 0.6  # 60% hit chance
            if hit:
                damage = random.randint(0, 20)
                return {"message": f"Hit enemy for {damage} damage!", "damage": damage}
            return {"message": "Missed attack!"}

        elif action == "capture":
            # Try to capture the flag
            if not session.get("has_flag"):
                # Try to take enemy flag
                success = random.random() < 0.4  # 40% success rate
                if success:
                    session["has_flag"] = True
                    return {"message": "Captured the enemy flag!"}
                return {"message": "Failed to capture the flag!"}
            else:
                # Try to score
                success = random.random() < 0.8  # 80% success rate if you have flag
                if success:
                    session["has_flag"] = False
                    score[team] += 1
                    return {"message": "Scored a point!", "score": score}
                return {"message": "Failed to score!"}

        elif action == "barricade":
            # Place or repair barricades
            success = random.random() < 0.9  # 90% success rate
            if success:
                return {"message": "Successfully placed barricade!"}
            return {"message": "Failed to place barricade!"}

        elif action == "special":
            # Use special items (explosive potions, rope, etc.)
            item = random.choice(["explosive_potion", "rope", "rocks"])
            success = random.random() < 0.7  # 70% success rate
            if success:
                return {"message": f"Successfully used {item}!", "item_used": item}
            return {"message": f"Failed to use {item}!"}

        return {"message": "Invalid action"}

    async def _process_fight_caves(self, session: Dict, action: str) -> Dict:
        """Process Fight Caves gameplay."""
        current_wave = session.get("wave", 1)
        enemies = self.fight_caves_waves[current_wave]

        if action == "attack":
            # Process combat
            damage_dealt = 0
            damage_taken = 0

            for enemy in enemies:
                # Player attacks enemy
                if random.random() < 0.6:  # 60% hit chance
                    damage = random.randint(0, session["max_hit"])
                    damage_dealt += damage
                    enemy.hp -= damage

                # Enemy attacks player
                if enemy.hp > 0 and random.random() < 0.5:
                    damage = random.randint(0, enemy.max_hit)
                    damage_taken += damage
                    session["player_hp"] -= damage

            # Check if wave completed
            if all(e.hp <= 0 for e in enemies):
                session["wave"] = current_wave + 1
                if current_wave == 63:  # Final wave
                    reward = self._calculate_rewards(MinigameType.FIGHT_CAVES, session)
                    self._end_session(session["player_id"])
                    return {
                        "message": "Congratulations! You have completed the Fight Caves!",
                        "rewards": reward,
                    }
                return {
                    "message": f"Wave {current_wave} completed! Starting wave {current_wave + 1}",
                    "damage_dealt": damage_dealt,
                    "damage_taken": damage_taken,
                    "wave": current_wave + 1,
                }

            return {
                "message": f"Fighting wave {current_wave}...",
                "damage_dealt": damage_dealt,
                "damage_taken": damage_taken,
                "hp": session["player_hp"],
            }

        elif action == "pray":
            session["prayer_points"] = min(99, session["prayer_points"] + 1)
            return {"message": "Restored prayer points", "prayer": session["prayer_points"]}

        return {"message": "Invalid action"}

    async def _process_inferno(self, session: Dict, action: str) -> Dict:
        """Process Inferno gameplay."""
        current_wave = session.get("wave", 1)
        enemies = self.inferno_waves[current_wave]

        if action == "attack":
            # Similar to Fight Caves but with more complex mechanics
            damage_dealt = 0
            damage_taken = 0

            # Process shield mechanics for Zuk
            if current_wave == 69:
                if not self._check_zuk_shield(session):
                    return {
                        "message": "You stepped out from behind the shield! Game Over.",
                        "game_over": True,
                    }

            # Process combat
            for enemy in enemies:
                if enemy.name == "Nibbler" and random.random() < 0.3:
                    # Nibblers attack pillars
                    session["pillar_hp"] -= 1
                    if session["pillar_hp"] <= 0:
                        return {
                            "message": "A pillar has been destroyed! Game Over.",
                            "game_over": True,
                        }

                # Combat calculations similar to Fight Caves
                # but with more complex mechanics...

            return {
                "message": f"Fighting Inferno wave {current_wave}...",
                "damage_dealt": damage_dealt,
                "damage_taken": damage_taken,
                "hp": session["player_hp"],
                "pillar_hp": session["pillar_hp"],
            }

        return {"message": "Invalid action"}

    def _check_zuk_shield(self, session: Dict) -> bool:
        """Check if player is safely behind Zuk's shield."""
        shield_position = session.get("shield_position", 0)
        player_position = session.get("player_position", 0)
        return abs(shield_position - player_position) <= 1

    def _process_nightmare_zone(self, session: Dict, action: str) -> Dict:
        """Process Nightmare Zone gameplay."""
        if action == "attack":
            points_gained = random.randint(200, 1000)
            session["points"] += points_gained

            if random.random() < 0.1:  # 10% chance for power-up
                power_up = random.choice(["power", "zapper", "recurrent"])
                return {
                    "message": f"Power-up obtained: {power_up}!",
                    "points": session["points"],
                    "power_up": power_up,
                }

            return {
                "message": "Fighting bosses...",
                "points": session["points"],
                "points_gained": points_gained,
            }

        elif action == "absorb":
            session["absorption"] = min(1000, session["absorption"] + 50)
            return {"message": "Drank absorption potion", "absorption": session["absorption"]}

        return {"message": "Invalid action"}

    def _process_tempoross(self, session: Dict, action: str) -> Dict:
        """Process Tempoross gameplay."""
        energy = session.get("energy", 100)
        fish = session.get("fish", 0)
        cooked_fish = session.get("cooked_fish", 0)
        storm_intensity = session.get("storm_intensity", 0)

        if action == "fish":
            # Fishing mechanics
            if energy < 10:
                return {"error": "Not enough energy to fish!"}

            catch_count = random.randint(1, 3)
            energy_cost = random.randint(5, 10)

            session["fish"] += catch_count
            session["energy"] = max(0, energy - energy_cost)

            return {
                "message": f"Caught {catch_count} fish!",
                "fish": session["fish"],
                "energy": session["energy"],
            }

        elif action == "cook":
            # Cooking mechanics
            if session["fish"] <= 0:
                return {"error": "No fish to cook!"}

            success = random.random() < 0.8  # 80% cooking success rate
            if success:
                cooked = min(5, session["fish"])
                session["fish"] -= cooked
                session["cooked_fish"] += cooked

                return {
                    "message": f"Cooked {cooked} fish!",
                    "cooked_fish": session["cooked_fish"],
                    "raw_fish": session["fish"],
                }
            return {"message": "Failed to cook fish!"}

        elif action == "attack":
            # Attack Tempoross with cooked fish
            if session["cooked_fish"] <= 0:
                return {"error": "No cooked fish to attack with!"}

            damage = session["cooked_fish"] * 2
            session["cooked_fish"] = 0
            session["storm_intensity"] = max(0, storm_intensity - damage)

            if session["storm_intensity"] <= 0:
                # Tempoross defeated
                reward = self._calculate_rewards(MinigameType.TEMPOROSS, session)
                self._end_session(session["player_id"])
                return {"message": "Tempoross has been defeated!", "rewards": reward}

            return {
                "message": f"Attacked Tempoross for {damage} damage!",
                "storm_intensity": session["storm_intensity"],
            }

        elif action == "dodge":
            # Dodge incoming wave attack
            success = random.random() < 0.7  # 70% dodge success rate
            if success:
                return {"message": "Successfully dodged the wave!"}

            # Take damage if dodge fails
            damage = random.randint(10, 20)
            session["energy"] = max(0, energy - damage)

            if session["energy"] <= 0:
                return {
                    "message": "You were swept away by the storm! Game Over.",
                    "game_over": True,
                }

            return {
                "message": f"Failed to dodge! Lost {damage} energy.",
                "energy": session["energy"],
            }

        elif action == "repair":
            # Repair damaged areas
            if energy < 15:
                return {"error": "Not enough energy to repair!"}

            session["energy"] -= 15
            success = random.random() < 0.9  # 90% repair success rate

            if success:
                return {"message": "Successfully repaired the area!", "energy": session["energy"]}
            return {"message": "Failed to repair the area!", "energy": session["energy"]}

        return {"message": "Invalid action"}

    def _process_volcanic_mine(self, session: Dict, action: str) -> Dict:
        """Process Volcanic Mine gameplay."""
        stability = session.get("stability", 100)
        gas_levels = session.get("gas_levels", 0)
        vent_status = session.get("vent_status", "closed")
        rock_type = session.get("rock_type", "unknown")
        points = session.get("points", 0)

        if action == "prospect":
            # Identify rock type
            if rock_type == "unknown":
                rock_type = random.choice(["gold", "silver", "platinum"])
                session["rock_type"] = rock_type
                return {"message": f"Found {rock_type} deposits!", "rock_type": rock_type}
            return {"message": f"Already identified as {rock_type} deposits"}

        elif action == "mine":
            # Mining mechanics
            if rock_type == "unknown":
                return {"error": "Need to prospect the rocks first!"}

            if stability < 20:
                return {"error": "Too unstable to mine!"}

            # Mine rocks and get points
            ore_amount = random.randint(1, 3)
            points_gained = ore_amount * (
                3 if rock_type == "gold" else 4 if rock_type == "silver" else 5  # platinum
            )

            session["points"] += points_gained
            session["stability"] -= random.randint(5, 10)

            return {
                "message": f"Mined {ore_amount} {rock_type} ore!",
                "points": session["points"],
                "stability": session["stability"],
            }

        elif action == "vent":
            # Manage gas vents
            if vent_status == "closed":
                session["vent_status"] = "open"
                session["gas_levels"] = max(0, gas_levels - 30)
                return {"message": "Opened gas vent!", "gas_levels": session["gas_levels"]}
            else:
                session["vent_status"] = "closed"
                return {"message": "Closed gas vent!", "vent_status": "closed"}

        elif action == "stabilize":
            # Stabilize the mine
            if stability > 80:
                return {"message": "Mine is already stable"}

            increase = random.randint(10, 20)
            session["stability"] = min(100, stability + increase)

            return {
                "message": f"Increased stability by {increase}%",
                "stability": session["stability"],
            }

        elif action == "check":
            # Check mine status
            return {
                "message": "Mine Status",
                "stability": stability,
                "gas_levels": gas_levels,
                "vent_status": vent_status,
                "rock_type": rock_type,
                "points": points,
            }

        # Process environmental changes
        gas_change = random.randint(-5, 10)
        session["gas_levels"] = max(0, min(100, gas_levels + gas_change))

        if session["gas_levels"] >= 100:
            return {"message": "Gas levels critical! Game Over.", "game_over": True}

        if session["stability"] <= 0:
            return {"message": "Mine collapsed! Game Over.", "game_over": True}

        return {"message": "Invalid action"}

    def _process_gauntlet(self, session: Dict, action: str) -> Dict:
        """Process Gauntlet gameplay."""
        resources = session.get(
            "resources", {"crystal_shards": 0, "ore": 0, "bark": 0, "herbs": 0, "fish": 0}
        )
        equipment = session.get(
            "equipment", {"weapon": None, "armor": None, "staff": None, "bow": None}
        )
        time_remaining = session.get("time_remaining", 600)  # 10 minutes in seconds
        hunllef_hp = session.get("hunllef_hp", 600)
        phase = session.get("phase", "preparation")

        if time_remaining <= 0:
            return {"message": "Time has run out! Game Over.", "game_over": True}

        if action == "gather":
            # Gather resources
            if phase != "preparation":
                return {"error": "Can only gather during preparation phase!"}

            resource_type = random.choice(["crystal_shards", "ore", "bark", "herbs", "fish"])
            amount = random.randint(1, 3)

            resources[resource_type] += amount
            session["resources"] = resources

            return {"message": f"Gathered {amount} {resource_type}!", "resources": resources}

        elif action == "craft":
            # Craft equipment
            if phase != "preparation":
                return {"error": "Can only craft during preparation phase!"}

            if resources["crystal_shards"] < 2:
                return {"error": "Need more crystal shards!"}

            # Craft different equipment types
            if "weapon" in action:
                if resources["ore"] < 3:
                    return {"error": "Need more ore!"}

                equipment["weapon"] = "crystal_halberd"
                resources["crystal_shards"] -= 2
                resources["ore"] -= 3

            elif "armor" in action:
                if resources["bark"] < 3:
                    return {"error": "Need more bark!"}

                equipment["armor"] = "crystal_armor"
                resources["crystal_shards"] -= 2
                resources["bark"] -= 3

            elif "staff" in action:
                if resources["herbs"] < 3:
                    return {"error": "Need more herbs!"}

                equipment["staff"] = "crystal_staff"
                resources["crystal_shards"] -= 2
                resources["herbs"] -= 3

            elif "bow" in action:
                if resources["bark"] < 3:
                    return {"error": "Need more bark!"}

                equipment["bow"] = "crystal_bow"
                resources["crystal_shards"] -= 2
                resources["bark"] -= 3

            session["resources"] = resources
            session["equipment"] = equipment

            return {"message": f"Crafted {action}!", "equipment": equipment, "resources": resources}

        elif action == "cook":
            # Cook fish
            if phase != "preparation":
                return {"error": "Can only cook during preparation phase!"}

            if resources["fish"] <= 0:
                return {"error": "No fish to cook!"}

            amount = min(resources["fish"], 5)
            resources["fish"] -= amount
            session["cooked_fish"] = session.get("cooked_fish", 0) + amount

            return {"message": f"Cooked {amount} fish!", "cooked_fish": session["cooked_fish"]}

        elif action == "start_boss":
            # Start Hunllef fight
            if phase != "preparation":
                return {"error": "Already fighting the Hunllef!"}

            if not (equipment["weapon"] or equipment["staff"] or equipment["bow"]):
                return {"error": "Need at least one weapon!"}

            if not equipment["armor"]:
                return {"error": "Need armor!"}

            session["phase"] = "boss"
            session["hunllef_style"] = random.choice(["melee", "magic", "ranged"])

            return {"message": "Started Hunllef fight!", "hunllef_style": session["hunllef_style"]}

        elif action == "attack":
            # Fight the Hunllef
            if phase != "boss":
                return {"error": "Not in boss fight!"}

            # Check if using correct attack style
            hunllef_style = session["hunllef_style"]
            player_weapon = None

            if equipment["weapon"] and action == "melee":
                player_weapon = "melee"
            elif equipment["staff"] and action == "magic":
                player_weapon = "magic"
            elif equipment["bow"] and action == "ranged":
                player_weapon = "ranged"

            if not player_weapon:
                return {"error": f"No weapon for {action} style!"}

            # Calculate damage
            damage = 0
            if player_weapon == hunllef_style:
                damage = random.randint(0, 13)  # Reduced damage when same style
            else:
                damage = random.randint(10, 25)

            session["hunllef_hp"] -= damage

            # Hunllef attacks back
            hunllef_damage = random.randint(0, 13)
            session["player_hp"] -= hunllef_damage

            # Change Hunllef's style occasionally
            if random.random() < 0.2:  # 20% chance
                session["hunllef_style"] = random.choice(["melee", "magic", "ranged"])

            if session["hunllef_hp"] <= 0:
                # Boss defeated
                reward = self._calculate_rewards(MinigameType.GAUNTLET, session)
                self._end_session(session["player_id"])
                return {
                    "message": "Congratulations! You have defeated the Hunllef!",
                    "rewards": reward,
                }

            if session["player_hp"] <= 0:
                return {"message": "You have been defeated! Game Over.", "game_over": True}

            return {
                "message": f"Dealt {damage} damage! Took {hunllef_damage} damage!",
                "hunllef_hp": session["hunllef_hp"],
                "player_hp": session["player_hp"],
                "hunllef_style": session["hunllef_style"],
            }

        elif action == "eat":
            # Eat cooked fish to heal
            if session.get("cooked_fish", 0) <= 0:
                return {"error": "No cooked fish to eat!"}

            heal_amount = random.randint(10, 20)
            session["cooked_fish"] -= 1
            session["player_hp"] = min(99, session["player_hp"] + heal_amount)

            return {
                "message": f"Healed {heal_amount} HP!",
                "player_hp": session["player_hp"],
                "cooked_fish": session["cooked_fish"],
            }

        # Update time
        session["time_remaining"] = max(0, time_remaining - 1)

        return {"message": "Invalid action"}

    def _calculate_rewards(self, minigame: MinigameType, session: Dict) -> MinigameRewards:
        """Calculate rewards for completing a minigame."""
        reward_info = self.rewards[minigame]

        # Calculate base rewards
        rewards = MinigameRewards(xp={}, items=[], points=0, tokens=0)

        # Add XP rewards
        for skill, amount in reward_info["xp"].items():
            if skill == "choice":
                rewards.xp["selected_skill"] = amount
            else:
                rewards.xp[skill] = amount

        # Add points/tokens
        if "points" in reward_info:
            min_points, max_points = reward_info["points"]
            rewards.points = random.randint(min_points, max_points)

        if "tokens" in reward_info:
            min_tokens, max_tokens = reward_info["tokens"]
            rewards.tokens = random.randint(min_tokens, max_tokens)

        # Roll for item rewards
        for item in reward_info.get("items", []):
            if "chance" in item:
                if random.random() < item["chance"]:
                    rewards.items.append({item["id"]: 1})

        return rewards

    def _end_session(self, player_id: int):
        """End a minigame session."""
        if player_id in self.active_sessions:
            del self.active_sessions[player_id]

    def _process_zalcano(self, session: Dict, action: str) -> Dict:
        """Process Zalcano gameplay."""
        phase = session.get("phase", "mining")
        heat_level = session.get("heat_level", 0)
        ores = session.get("ores", 0)
        refined_ores = session.get("refined_ores", 0)
        shield_active = session.get("shield_active", True)

        if action == "mine":
            if phase != "mining":
                return {"error": "Can only mine during mining phase!"}

            if shield_active:
                return {"error": "Need to break Zalcano's shield first!"}

            # Mining mechanics
            success = random.random() < 0.7  # 70% success rate
            if success:
                amount = random.randint(1, 3)
                session["ores"] += amount
                return {"message": f"Mined {amount} tephra ores!", "ores": session["ores"]}
            return {"message": "Failed to mine ore!"}

        elif action == "heat":
            if phase != "mining":
                return {"error": "Can only heat during mining phase!"}

            if session["ores"] <= 0:
                return {"error": "No ores to heat!"}

            # Heating mechanics
            session["heat_level"] = min(100, heat_level + random.randint(10, 20))
            session["ores"] -= 1

            if session["heat_level"] >= 100:
                session["phase"] = "smithing"
                return {"message": "Ores fully heated! Ready for smithing.", "phase": "smithing"}

            return {
                "message": f'Heating ores... ({session["heat_level"]}%)',
                "heat_level": session["heat_level"],
            }

        elif action == "smith":
            if phase != "smithing":
                return {"error": "Can only smith during smithing phase!"}

            if heat_level < 100:
                return {"error": "Ores not hot enough!"}

            # Smithing mechanics
            success = random.random() < 0.8  # 80% success rate
            if success:
                refined = random.randint(1, 2)
                session["refined_ores"] += refined
                session["heat_level"] = 0
                session["phase"] = "throwing"

                return {
                    "message": f"Refined {refined} ores! Ready to throw.",
                    "refined_ores": session["refined_ores"],
                    "phase": "throwing",
                }
            return {"message": "Failed to refine ores!"}

        elif action == "throw":
            if phase != "throwing":
                return {"error": "Can only throw during throwing phase!"}

            if refined_ores <= 0:
                return {"error": "No refined ores to throw!"}

            # Throwing mechanics
            damage = refined_ores * random.randint(10, 20)
            session["refined_ores"] = 0
            session["boss_hp"] = max(0, session.get("boss_hp", 1000) - damage)

            if session["boss_hp"] <= 0:
                # Boss defeated
                reward = self._calculate_rewards(MinigameType.ZALCANO, session)
                self._end_session(session["player_id"])
                return {"message": "Zalcano has been defeated!", "rewards": reward}

            # Boss attacks back
            if random.random() < 0.3:  # 30% chance for special attack
                attack_type = random.choice(["falling_rocks", "fire_wall", "crystal_rain"])
                damage_taken = random.randint(10, 30)
                session["player_hp"] -= damage_taken

                if session["player_hp"] <= 0:
                    return {"message": f"Killed by {attack_type}! Game Over.", "game_over": True}

                return {
                    "message": f"Hit for {damage} damage! Took {damage_taken} damage from {attack_type}!",
                    "boss_hp": session["boss_hp"],
                    "player_hp": session["player_hp"],
                }

            session["phase"] = "mining"
            session["shield_active"] = True

            return {
                "message": f"Hit for {damage} damage! Zalcano's shield is back up.",
                "boss_hp": session["boss_hp"],
            }

        elif action == "dodge":
            # Dodge incoming attack
            success = random.random() < 0.7  # 70% dodge success rate
            if success:
                return {"message": "Successfully dodged the attack!"}

            damage = random.randint(5, 15)
            session["player_hp"] -= damage

            if session["player_hp"] <= 0:
                return {"message": "You have been defeated! Game Over.", "game_over": True}

            return {
                "message": f"Failed to dodge! Took {damage} damage.",
                "player_hp": session["player_hp"],
            }

        return {"message": "Invalid action"}

    def _process_soul_wars(self, session: Dict, action: str) -> Dict:
        """Process Soul Wars gameplay."""
        team = session.get("team", "blue")
        avatar_hp = session.get("avatar_hp", {"blue": 100, "red": 100})
        fragments = session.get("soul_fragments", 0)
        controlled_obelisk = session.get("obelisk_control", None)

        if action == "attack_players":
            # PvP combat
            hit = random.random() < 0.6  # 60% hit chance
            if hit:
                damage = random.randint(0, 20)
                return {"message": f"Hit enemy player for {damage} damage!", "damage": damage}
            return {"message": "Missed attack!"}

        elif action == "attack_slayer":
            # Attack slayer creatures
            success = random.random() < 0.7  # 70% success rate
            if success:
                fragments_gained = random.randint(1, 3)
                session["soul_fragments"] += fragments_gained
                return {
                    "message": f"Gained {fragments_gained} soul fragments!",
                    "fragments": session["soul_fragments"],
                }
            return {"message": "Failed to defeat creature!"}

        elif action == "capture_obelisk":
            # Try to capture the obelisk
            if fragments < 5:
                return {"error": "Need at least 5 soul fragments!"}

            success = random.random() < 0.5  # 50% capture rate
            if success:
                session["soul_fragments"] -= 5
                session["obelisk_control"] = team
                return {"message": f"Captured the obelisk for {team} team!", "obelisk": team}
            return {"message": "Failed to capture obelisk!"}

        elif action == "attack_avatar":
            # Attack enemy avatar
            if controlled_obelisk != team:
                return {"error": "Your team must control the obelisk!"}

            enemy_team = "red" if team == "blue" else "blue"
            damage = random.randint(1, 5)
            avatar_hp[enemy_team] -= damage

            if avatar_hp[enemy_team] <= 0:
                # Game won
                reward = self._calculate_rewards(MinigameType.SOUL_WARS, session)
                self._end_session(session["player_id"])
                return {"message": f"{team.title()} team wins!", "rewards": reward}

            return {"message": f"Hit enemy avatar for {damage} damage!", "avatar_hp": avatar_hp}

        elif action == "bury_bones":
            # Bury bones for prayer points
            success = random.random() < 0.9  # 90% success rate
            if success:
                prayer_gained = random.randint(10, 20)
                session["prayer_points"] = min(99, session.get("prayer_points", 0) + prayer_gained)
                return {
                    "message": f"Restored {prayer_gained} prayer points!",
                    "prayer": session["prayer_points"],
                }
            return {"message": "Failed to bury bones!"}

        elif action == "use_bandages":
            # Heal with bandages
            heal_amount = random.randint(10, 20)
            session["player_hp"] = min(99, session.get("player_hp", 0) + heal_amount)

            return {"message": f"Healed for {heal_amount} HP!", "hp": session["player_hp"]}

        return {"message": "Invalid action"}

    def _process_mahogany_homes(self, session: Dict, action: str) -> Dict:
        """Process Mahogany Homes gameplay."""
        contract = session.get("contract", None)
        materials = session.get(
            "materials", {"planks": 0, "steel_bars": 0, "nails": 0, "bolt_of_cloth": 0}
        )
        repairs_made = session.get("repairs_made", 0)
        contract_progress = session.get("contract_progress", 0)

        if action == "get_contract":
            if contract:
                return {"error": "You already have an active contract!"}

            # Generate random contract
            difficulty = random.choice(["novice", "adept", "expert"])
            location = random.choice(["varrock", "falador", "hosidius", "prifddinas"])

            session["contract"] = {
                "difficulty": difficulty,
                "location": location,
                "repairs_needed": 3
                if difficulty == "novice"
                else 4
                if difficulty == "adept"
                else 5,
            }

            return {
                "message": f"Received {difficulty} contract in {location}!",
                "contract": session["contract"],
            }

        elif action == "check_materials":
            if not contract:
                return {"error": "You need to get a contract first!"}

            return {"message": "Current materials:", "materials": materials}

        elif action == "repair":
            if not contract:
                return {"error": "You need to get a contract first!"}

            # Check materials based on difficulty
            required_materials = {
                "novice": {"planks": 2, "steel_bars": 1, "nails": 5},
                "adept": {"planks": 3, "steel_bars": 2, "nails": 8, "bolt_of_cloth": 1},
                "expert": {"planks": 4, "steel_bars": 3, "nails": 12, "bolt_of_cloth": 2},
            }[contract["difficulty"]]

            # Check if player has required materials
            for material, amount in required_materials.items():
                if materials.get(material, 0) < amount:
                    return {"error": f"Need {amount} {material} to repair!"}

            # Consume materials
            for material, amount in required_materials.items():
                materials[material] -= amount

            # Repair success chance based on difficulty
            success_chance = {"novice": 0.9, "adept": 0.8, "expert": 0.7}[contract["difficulty"]]

            if random.random() < success_chance:
                repairs_made += 1
                contract_progress = (repairs_made / contract["repairs_needed"]) * 100

                session["repairs_made"] = repairs_made
                session["contract_progress"] = contract_progress
                session["materials"] = materials

                if repairs_made >= contract["repairs_needed"]:
                    # Contract completed
                    reward = self._calculate_rewards(MinigameType.MAHOGANY_HOMES, session)
                    self._end_session(session["player_id"])
                    return {"message": "Contract completed!", "rewards": reward}

                return {
                    "message": f"Successfully made repair! ({contract_progress:.1f}% complete)",
                    "repairs_made": repairs_made,
                    "progress": contract_progress,
                }

            return {"message": "Failed to make repair!", "materials": materials}

        elif action == "add_materials":
            # Simulate adding materials to inventory
            material_type = random.choice(list(materials.keys()))
            amount = random.randint(1, 5)

            materials[material_type] += amount
            session["materials"] = materials

            return {"message": f"Added {amount} {material_type}!", "materials": materials}

        return {"message": "Invalid action"}

    def _process_hallowed_sepulchre(self, session: Dict, action: str) -> Dict:
        """Process Hallowed Sepulchre gameplay."""
        floor = session.get("floor", 1)
        time_remaining = session.get("time_remaining", 300)  # 5 minutes per floor
        obstacles_cleared = session.get("obstacles_cleared", 0)
        marks_collected = session.get("marks", 0)
        coffins_looted = session.get("coffins_looted", set())

        if time_remaining <= 0:
            return {"message": "Time has run out! Game Over.", "game_over": True}

        if action == "run_floor":
            # Progress through floor obstacles
            if obstacles_cleared >= 5:  # Each floor has 5 obstacles
                return {"error": "Floor already completed! Use start_next_floor to proceed."}

            # Calculate success chance based on floor level
            success_chance = {
                1: 0.9,  # 90% success rate on floor 1
                2: 0.85,
                3: 0.8,
                4: 0.75,
                5: 0.7,  # 70% success rate on floor 5
            }[floor]

            if random.random() < success_chance:
                obstacles_cleared += 1
                session["obstacles_cleared"] = obstacles_cleared

                # Award marks randomly
                if random.random() < 0.3:  # 30% chance for marks
                    marks_gained = random.randint(1, 3)
                    marks_collected += marks_gained
                    session["marks"] = marks_collected

                if obstacles_cleared >= 5:
                    return {
                        "message": f"Floor {floor} completed! Ready for next floor.",
                        "obstacles_cleared": obstacles_cleared,
                        "marks": marks_collected,
                    }

                return {
                    "message": f"Cleared obstacle! ({obstacles_cleared}/5)",
                    "obstacles_cleared": obstacles_cleared,
                    "marks": marks_collected,
                }

            # Failed obstacle
            time_penalty = random.randint(10, 20)
            session["time_remaining"] = max(0, time_remaining - time_penalty)

            return {
                "message": f"Failed obstacle! Lost {time_penalty} seconds.",
                "time_remaining": session["time_remaining"],
            }

        elif action == "start_next_floor":
            if obstacles_cleared < 5:
                return {"error": "Need to complete current floor first!"}

            if floor >= 5:
                # Completed all floors
                reward = self._calculate_rewards(MinigameType.HALLOWED_SEPULCHRE, session)
                self._end_session(session["player_id"])
                return {
                    "message": "Congratulations! You have completed the Hallowed Sepulchre!",
                    "rewards": reward,
                }

            # Move to next floor
            session["floor"] = floor + 1
            session["obstacles_cleared"] = 0
            session["time_remaining"] = time_remaining + 120  # Add 2 minutes for next floor

            return {
                "message": f"Starting floor {floor + 1}!",
                "floor": floor + 1,
                "time_remaining": session["time_remaining"],
            }

        elif action == "loot_coffin":
            # Loot grand coffins for extra rewards
            if obstacles_cleared < 5:
                return {"error": "Need to complete floor before looting!"}

            coffin_id = f"floor_{floor}_coffin"
            if coffin_id in coffins_looted:
                return {"error": "Already looted this floor's coffin!"}

            # Time cost for looting
            session["time_remaining"] = max(0, time_remaining - 15)
            coffins_looted.add(coffin_id)
            session["coffins_looted"] = coffins_looted

            # Random valuable loot
            if random.random() < 0.1:  # 10% chance for rare loot
                loot = random.choice(
                    ["ring_of_endurance_piece", "strange_old_lockpick", "dark_dye"]
                )
                return {
                    "message": f"Found rare item: {loot}!",
                    "loot": loot,
                    "time_remaining": session["time_remaining"],
                }

            # Common loot
            marks_gained = random.randint(3, 8)
            marks_collected += marks_gained
            session["marks"] = marks_collected

            return {
                "message": f"Looted coffin for {marks_gained} marks!",
                "marks": marks_collected,
                "time_remaining": session["time_remaining"],
            }

        elif action == "check_time":
            minutes = time_remaining // 60
            seconds = time_remaining % 60
            return {
                "message": f"Time remaining: {minutes}:{seconds:02d}",
                "time_remaining": time_remaining,
            }

        # Update time
        session["time_remaining"] = max(0, time_remaining - 1)

        return {"message": "Invalid action"}

    def _process_fishing_trawler(self, session: Dict, action: str) -> Dict:
        """Process Fishing Trawler gameplay."""
        water_level = session.get("water_level", 0)
        net_status = session.get("net_status", 100)
        fish_caught = session.get("fish_caught", 0)
        time_remaining = session.get("time_remaining", 600)  # 10 minutes

        if time_remaining <= 0:
            # End game and calculate rewards
            reward = self._calculate_rewards(MinigameType.FISHING_TRAWLER, session)
            self._end_session(session["player_id"])
            return {"message": f"Trip complete! Caught {fish_caught} fish!", "rewards": reward}

        if action == "bail":
            # Bail water from the boat
            if water_level <= 0:
                return {"message": "No water to bail!"}

            amount = random.randint(5, 15)
            session["water_level"] = max(0, water_level - amount)

            return {
                "message": f"Bailed {amount} water from the boat!",
                "water_level": session["water_level"],
            }

        elif action == "repair":
            # Repair fishing net
            if net_status >= 100:
                return {"message": "Net doesn't need repairs!"}

            repair_amount = random.randint(10, 25)
            session["net_status"] = min(100, net_status + repair_amount)

            return {
                "message": f'Repaired the net! ({session["net_status"]}% integrity)',
                "net_status": session["net_status"],
            }

        elif action == "check":
            # Check boat status
            return {
                "message": "Boat Status",
                "water_level": water_level,
                "net_status": net_status,
                "fish_caught": fish_caught,
                "time_remaining": time_remaining,
            }

        # Process environmental changes
        # 1. Water level increases
        water_increase = random.randint(0, 10)
        session["water_level"] += water_increase

        # 2. Net takes damage
        net_damage = random.randint(0, 5)
        session["net_status"] = max(0, net_status - net_damage)

        # 3. Catch fish if conditions are good
        if water_level < 50 and net_status > 50:
            fish_gained = random.randint(1, 3)
            session["fish_caught"] += fish_gained

        # 4. Update time
        session["time_remaining"] = max(0, time_remaining - 1)

        # Check failure conditions
        if water_level >= 100:
            return {"message": "The boat has sunk! Game Over.", "game_over": True}

        if net_status <= 0:
            return {"message": "The net is completely destroyed! Game Over.", "game_over": True}

        return {
            "message": "Continuing to fish...",
            "water_level": session["water_level"],
            "net_status": session["net_status"],
            "fish_caught": session["fish_caught"],
        }

    def _process_trouble_brewing(self, session: Dict, action: str) -> Dict:
        """Process Trouble Brewing gameplay."""
        resources = session.get(
            "resources", {"water": 0, "sugar": 0, "hops": 0, "buckets": 5, "the_stuff": 0}
        )
        rum_progress = session.get("rum_progress", 0)
        sabotage_points = session.get("sabotage_points", 0)
        pieces_of_eight = session.get("pieces_of_eight", 0)
        time_remaining = session.get("time_remaining", 1200)  # 20 minutes

        if time_remaining <= 0:
            # End game and calculate rewards
            reward = self._calculate_rewards(MinigameType.TROUBLE_BREWING, session)
            self._end_session(session["player_id"])
            return {
                "message": f"Game complete! Earned {pieces_of_eight} Pieces of Eight!",
                "rewards": reward,
            }

        if action == "get_water":
            # Collect water with buckets
            if resources["buckets"] <= 0:
                return {"error": "No empty buckets!"}

            amount = min(resources["buckets"], random.randint(1, 3))
            resources["water"] += amount
            resources["buckets"] -= amount

            return {"message": f"Collected {amount} buckets of water!", "resources": resources}

        elif action == "get_sugar":
            # Collect sugar from sugar cane
            amount = random.randint(1, 3)
            resources["sugar"] += amount

            return {"message": f"Collected {amount} sugar!", "resources": resources}

        elif action == "get_hops":
            # Collect hops from hop plants
            amount = random.randint(1, 2)
            resources["hops"] += amount

            return {"message": f"Collected {amount} hops!", "resources": resources}

        elif action == "brew":
            # Brew rum
            if resources["water"] < 1 or resources["sugar"] < 1 or resources["hops"] < 1:
                return {"error": "Missing ingredients for brewing!"}

            # Consume resources
            resources["water"] -= 1
            resources["sugar"] -= 1
            resources["hops"] -= 1
            resources["buckets"] += 1  # Get empty bucket back

            # Brewing success chance
            success = random.random() < 0.8  # 80% success rate
            if success:
                progress_amount = random.randint(10, 20)
                session["rum_progress"] += progress_amount

                if session["rum_progress"] >= 100:
                    # Rum batch complete
                    session["rum_progress"] = 0
                    pieces_gained = random.randint(2, 5)
                    session["pieces_of_eight"] += pieces_gained

                    return {
                        "message": f"Rum batch complete! Earned {pieces_gained} Pieces of Eight!",
                        "pieces_of_eight": session["pieces_of_eight"],
                    }

                return {
                    "message": f'Brewing in progress... ({session["rum_progress"]}%)',
                    "rum_progress": session["rum_progress"],
                }
            return {"message": "Brewing failed!"}

        elif action == "make_stuff":
            # Create 'The Stuff' (brewing catalyst)
            if resources["water"] < 2 or resources["hops"] < 2:
                return {"error": "Need 2 water and 2 hops to make The Stuff!"}

            resources["water"] -= 2
            resources["hops"] -= 2
            resources["buckets"] += 2  # Get empty buckets back
            resources["the_stuff"] += 1

            return {"message": "Created 1 The Stuff!", "resources": resources}

        elif action == "sabotage":
            # Attempt to sabotage opposing team
            success = random.random() < 0.6  # 60% success rate
            if success:
                points = random.randint(1, 3)
                session["sabotage_points"] += points
                session["pieces_of_eight"] += points

                return {
                    "message": f"Successful sabotage! Earned {points} points!",
                    "sabotage_points": session["sabotage_points"],
                    "pieces_of_eight": session["pieces_of_eight"],
                }
            return {"message": "Sabotage attempt failed!"}

        elif action == "repair":
            # Repair equipment damaged by opposing team
            success = random.random() < 0.8  # 80% success rate
            if success:
                points = random.randint(1, 2)
                session["pieces_of_eight"] += points

                return {
                    "message": f"Repairs complete! Earned {points} points!",
                    "pieces_of_eight": session["pieces_of_eight"],
                }
            return {"message": "Failed to repair equipment!"}

        # Update time
        session["time_remaining"] = max(0, time_remaining - 1)

        # Random events
        if random.random() < 0.1:  # 10% chance per tick
            event = random.choice(["equipment_break", "monkey_steal", "storm"])

            if event == "equipment_break":
                return {"message": "Equipment has been damaged! Use repair to fix it."}
            elif event == "monkey_steal":
                if resources["sugar"] > 0:
                    resources["sugar"] -= 1
                    return {"message": "A monkey stole some sugar!", "resources": resources}
            elif event == "storm":
                if resources["water"] > 0:
                    lost = random.randint(1, resources["water"])
                    resources["water"] -= lost
                    resources["buckets"] += lost
                    return {"message": f"Storm spilled {lost} water!", "resources": resources}

        return {
            "message": "Continuing to brew...",
            "resources": resources,
            "rum_progress": rum_progress,
            "pieces_of_eight": pieces_of_eight,
        }

    def _process_pyramid_plunder(self, session: Dict, action: str) -> Dict:
        """Process Pyramid Plunder gameplay."""
        current_room = session.get("room", 1)
        time_remaining = session.get("time_remaining", 300)  # 5 minutes
        artifacts_found = session.get("artifacts", 0)
        room_looted = session.get("room_looted", {})

        if time_remaining <= 0:
            # End game and calculate rewards
            reward = self._calculate_rewards(MinigameType.PYRAMID_PLUNDER, session)
            self._end_session(session["player_id"])
            return {"message": f"Time's up! Found {artifacts_found} artifacts!", "rewards": reward}

        if action == "search_urn":
            # Search urns for artifacts
            if "urns" in room_looted.get(current_room, []):
                return {"error": "Already searched all urns in this room!"}

            # Success chance increases with room number
            success_chance = 0.3 + (current_room * 0.1)  # 40% in room 1, up to 100% in room 8

            if random.random() < success_chance:
                artifacts_gained = random.randint(1, 2)
                session["artifacts"] = artifacts_found + artifacts_gained

                # Random chance for special items
                if random.random() < 0.01:  # 1% chance
                    special_item = random.choice(
                        ["pharaohs_sceptre", "golden_scarab", "golden_idol"]
                    )
                    return {
                        "message": f"Found {artifacts_gained} artifacts and a {special_item}!",
                        "artifacts": session["artifacts"],
                        "special_item": special_item,
                    }

                return {
                    "message": f"Found {artifacts_gained} artifacts!",
                    "artifacts": session["artifacts"],
                }

            # Check for mummy or snake
            if random.random() < 0.2:  # 20% chance
                damage = random.randint(1, 8)
                session["player_hp"] -= damage

                if session["player_hp"] <= 0:
                    return {"message": "You have been defeated! Game Over.", "game_over": True}

                return {
                    "message": f"Triggered a trap! Took {damage} damage.",
                    "hp": session["player_hp"],
                }

            return {"message": "Found nothing in the urn."}

        elif action == "search_chest":
            # Search grand chests (better rewards but higher risk)
            if "chest" in room_looted.get(current_room, []):
                return {"error": "Already searched the chest in this room!"}

            # Higher success chance but also higher risk
            success_chance = 0.4 + (current_room * 0.05)

            if random.random() < success_chance:
                artifacts_gained = random.randint(2, 4)
                session["artifacts"] = artifacts_found + artifacts_gained

                # Better chance for special items
                if random.random() < 0.05:  # 5% chance
                    special_item = random.choice(
                        ["pharaohs_sceptre", "golden_statuette", "jewelled_golden_statuette"]
                    )
                    return {
                        "message": f"Found {artifacts_gained} artifacts and a {special_item}!",
                        "artifacts": session["artifacts"],
                        "special_item": special_item,
                    }

                return {
                    "message": f"Found {artifacts_gained} artifacts in the chest!",
                    "artifacts": session["artifacts"],
                }

            # Higher damage from chest traps
            damage = random.randint(5, 15)
            session["player_hp"] -= damage

            if session["player_hp"] <= 0:
                return {"message": "You have been defeated! Game Over.", "game_over": True}

            return {
                "message": f"Triggered a chest trap! Took {damage} damage.",
                "hp": session["player_hp"],
            }

        elif action == "search_sarcophagus":
            # Search sarcophagus (highest risk/reward)
            if "sarcophagus" in room_looted.get(current_room, []):
                return {"error": "Already searched the sarcophagus in this room!"}

            # Highest rewards but also highest risk
            success_chance = 0.3 + (current_room * 0.05)

            if random.random() < success_chance:
                artifacts_gained = random.randint(3, 6)
                session["artifacts"] = artifacts_found + artifacts_gained

                # Best chance for special items
                if random.random() < 0.1:  # 10% chance
                    special_item = random.choice(["pharaohs_sceptre", "jewelled_golden_statuette"])
                    return {
                        "message": f"Found {artifacts_gained} artifacts and a {special_item}!",
                        "artifacts": session["artifacts"],
                        "special_item": special_item,
                    }

                return {
                    "message": f"Found {artifacts_gained} artifacts in the sarcophagus!",
                    "artifacts": session["artifacts"],
                }

            # Highest damage from sarcophagus traps
            damage = random.randint(10, 20)
            session["player_hp"] -= damage

            if session["player_hp"] <= 0:
                return {"message": "You have been defeated! Game Over.", "game_over": True}

            return {
                "message": f"Awakened a mummy! Took {damage} damage.",
                "hp": session["player_hp"],
            }

        elif action == "next_room":
            # Move to next room
            if current_room >= 8:
                return {"error": "Already in the final room!"}

            # Need to have searched at least one container in current room
            if current_room not in room_looted:
                return {"error": "Search at least one container before moving to the next room!"}

            session["room"] = current_room + 1
            return {"message": f"Entered room {current_room + 1}!", "room": session["room"]}

        elif action == "check_time":
            minutes = time_remaining // 60
            seconds = time_remaining % 60
            return {
                "message": f"Time remaining: {minutes}:{seconds:02d}",
                "time_remaining": time_remaining,
            }

        # Update time
        session["time_remaining"] = max(0, time_remaining - 1)

        # Mark containers as looted
        if action.startswith("search_"):
            container_type = action.split("_")[1]
            if current_room not in room_looted:
                room_looted[current_room] = set()
            room_looted[current_room].add(container_type)
            session["room_looted"] = room_looted

        return {
            "message": "Exploring the pyramid...",
            "room": current_room,
            "artifacts": artifacts_found,
            "time_remaining": time_remaining,
        }
