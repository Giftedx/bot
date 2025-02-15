import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, Dict, List, TypedDict
from enum import Enum
import random
import asyncio
from ..lib.combat.combat_manager import CombatManager
from ..lib.data.game_data import GameData
from ..lib.database.db_manager import DatabaseManager

class CombatStyle(str, Enum):
    ACCURATE = "accurate"
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    CONTROLLED = "controlled"
    RAPID = "rapid"
    LONGRANGE = "longrange"

class CombatStats(TypedDict):
    attack: int
    strength: int
    defence: int
    ranged: int
    magic: int
    prayer: int
    hitpoints: int

class CombatCommands(commands.Cog):
    """Combat System Commands"""

    def __init__(self, bot: commands.Bot, db: DatabaseManager, game_data: GameData):
        self.bot = bot
        self.combat_manager = CombatManager(db, game_data)
        self.game_data = game_data
        self.active_fights = {}

    @app_commands.command(name='combat_stats', description='View your combat stats')
    async def view_combat_stats(self, interaction: discord.Interaction):
        """View your combat statistics"""
        # Get player's combat stats from database
        stats = await self.get_combat_stats(interaction.user.id)
        if not stats:
            await interaction.response.send_message(
                "You don't have any combat stats yet!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"{interaction.user.name}'s Combat Stats",
            color=discord.Color.red()
        )

        # Combat stats
        stats_text = (
            f"⚔️ Attack: {stats['attack']}\n"
            f"💪 Strength: {stats['strength']}\n"
            f"🛡️ Defence: {stats['defence']}\n"
            f"🏹 Ranged: {stats['ranged']}\n"
            f"🔮 Magic: {stats['magic']}\n"
            f"✨ Prayer: {stats['prayer']}\n"
            f"❤️ Hitpoints: {stats['hitpoints']}"
        )
        embed.add_field(name="Stats", value=stats_text, inline=True)

        # Combat level
        combat_level = self.calculate_combat_level(stats)
        embed.add_field(name="Combat Level", value=str(combat_level), inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='attack_style', description='Change your combat attack style')
    async def change_attack_style(
        self,
        interaction: discord.Interaction,
        style: CombatStyle
    ):
        """Change your combat attack style"""
        # Update player's attack style in database
        success = await self.set_attack_style(interaction.user.id, style)
        if not success:
            await interaction.response.send_message(
                "Failed to change attack style. Please try again.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Attack Style Changed",
            description=f"Your attack style is now set to {style.value.title()}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='prayer', description='Toggle prayer effects')
    async def toggle_prayer(
        self,
        interaction: discord.Interaction,
        prayer: str,
        enabled: bool
    ):
        """Toggle prayer effects on/off"""
        # Get player's prayer points
        prayer_points = await self.get_prayer_points(interaction.user.id)
        if prayer_points <= 0:
            await interaction.response.send_message(
                "You have no prayer points! Recharge at an altar.",
                ephemeral=True
            )
            return

        # Update prayer status
        success = await self.set_prayer_status(interaction.user.id, prayer, enabled)
        if not success:
            await interaction.response.send_message(
                f"Failed to {'activate' if enabled else 'deactivate'} {prayer}. Please try again.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Prayer Status Updated",
            description=f"{prayer.title()} is now {'activated' if enabled else 'deactivated'}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Prayer Points", value=str(prayer_points))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='special_attack', description='Use your weapon\'s special attack')
    async def special_attack(self, interaction: discord.Interaction):
        """Use your weapon's special attack"""
        # Get player's special attack energy
        energy = await self.get_special_attack_energy(interaction.user.id)
        if energy < 50:  # Most special attacks use 50% energy
            await interaction.response.send_message(
                f"Not enough special attack energy! Current energy: {energy}%",
                ephemeral=True
            )
            return

        # Get player's equipped weapon
        weapon = await self.get_equipped_weapon(interaction.user.id)
        if not weapon or not weapon.get("special_attack"):
            await interaction.response.send_message(
                "Your current weapon has no special attack!",
                ephemeral=True
            )
            return

        # Use special attack
        success = await self.use_special_attack(interaction.user.id)
        if not success:
            await interaction.response.send_message(
                "Failed to use special attack. Please try again.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Special Attack",
            description=f"Used {weapon['name']}'s special attack!",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="Energy Remaining",
            value=f"{energy - 50}%"
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='restore', description='Restore your combat stats')
    async def restore_stats(self, interaction: discord.Interaction):
        """Restore your combat stats to their base levels"""
        # Restore stats in database
        success = await self.restore_combat_stats(interaction.user.id)
        if not success:
            await interaction.response.send_message(
                "Failed to restore stats. Please try again.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Stats Restored",
            description="Your combat stats have been restored to their base levels.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='eat', description='Eat food to heal')
    async def eat_food(
        self,
        interaction: discord.Interaction,
        food: str
    ):
        """Eat food to restore hitpoints"""
        # Check if player has the food
        has_food = await self.check_inventory(interaction.user.id, food)
        if not has_food:
            await interaction.response.send_message(
                f"You don't have any {food}!",
                ephemeral=True
            )
            return

        # Get food healing amount
        healing = await self.get_food_healing(food)
        if healing is None:
            await interaction.response.send_message(
                f"Invalid food item: {food}",
                ephemeral=True
            )
            return

        # Heal player
        success, new_hp = await self.heal_player(interaction.user.id, healing)
        if not success:
            await interaction.response.send_message(
                "Failed to eat food. Please try again.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Ate Food",
            description=f"You eat the {food}.",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Healed",
            value=f"+{healing} HP"
        )
        embed.add_field(
            name="Current HP",
            value=str(new_hp)
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='potion', description='Drink a potion')
    async def drink_potion(
        self,
        interaction: discord.Interaction,
        potion: str
    ):
        """Drink a potion to boost your stats"""
        # Check if player has the potion
        has_potion = await self.check_inventory(interaction.user.id, potion)
        if not has_potion:
            await interaction.response.send_message(
                f"You don't have any {potion}!",
                ephemeral=True
            )
            return

        # Get potion effects
        effects = await self.get_potion_effects(potion)
        if not effects:
            await interaction.response.send_message(
                f"Invalid potion: {potion}",
                ephemeral=True
            )
            return

        # Apply potion effects
        success, new_stats = await self.apply_potion(interaction.user.id, effects)
        if not success:
            await interaction.response.send_message(
                "Failed to drink potion. Please try again.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Drank Potion",
            description=f"You drink the {potion}.",
            color=discord.Color.green()
        )

        # Show stat changes
        changes = []
        for stat, boost in effects.items():
            changes.append(f"{stat.title()}: {boost:+d}")
        embed.add_field(
            name="Effects",
            value="\n".join(changes)
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="monsters")
    async def monsters_command(self, interaction: discord.Interaction, min_level: Optional[int] = None, max_level: Optional[int] = None):
        """List available monsters to fight"""
        monsters = self.game_data.get_monsters_by_level_range(min_level, max_level)
        
        # Group monsters by difficulty
        novice = []
        intermediate = []
        advanced = []
        boss = []
        
        for monster in monsters:
            if monster["combat_level"] < 50:
                novice.append(monster)
            elif monster["combat_level"] < 100:
                intermediate.append(monster)
            elif monster["combat_level"] < 200:
                advanced.append(monster)
            else:
                boss.append(monster)

        embed = discord.Embed(title="Available Monsters", color=discord.Color.blue())
        
        if novice:
            monster_list = "\n".join([f"• {m['name']} (Level {m['combat_level']})" for m in novice])
            embed.add_field(name="Novice (1-49)", value=monster_list, inline=False)
            
        if intermediate:
            monster_list = "\n".join([f"• {m['name']} (Level {m['combat_level']})" for m in intermediate])
            embed.add_field(name="Intermediate (50-99)", value=monster_list, inline=False)
            
        if advanced:
            monster_list = "\n".join([f"• {m['name']} (Level {m['combat_level']})" for m in advanced])
            embed.add_field(name="Advanced (100-199)", value=monster_list, inline=False)
            
        if boss:
            monster_list = "\n".join([f"• {m['name']} (Level {m['combat_level']})" for m in boss])
            embed.add_field(name="Boss (200+)", value=monster_list, inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="fight")
    async def fight_command(self, interaction: discord.Interaction, monster_name: str):
        """Start a fight with a monster"""
        monster = self.game_data.get_monster_by_name(monster_name)
        if not monster:
            await interaction.response.send_message(f"Monster '{monster_name}' not found.")
            return

        # Get monster metadata
        monster_id = monster["name"].lower().replace(" ", "_")
        metadata = self.game_data.get_wiki_metadata("monsters", monster_id)

        embed = discord.Embed(
            title=f"Fight: {monster['name']}", 
            color=discord.Color.red()
        )

        if metadata:
            embed.url = metadata["wiki_url"]
            embed.set_thumbnail(url=metadata["image_url"])
            embed.description = metadata["examine"]

            # Add location information if available
            if "location" in metadata:
                embed.add_field(
                    name="Locations", 
                    value="\n".join([f"• {loc}" for loc in metadata["location"]]),
                    inline=False
                )

            # Add additional info for bosses
            if "additional_info" in metadata:
                if "boss_info" in metadata["additional_info"]:
                    boss_info = metadata["additional_info"]["boss_info"]
                    recommended_stats = boss_info["recommended_stats"]
                    embed.add_field(
                        name="Recommended Stats",
                        value="\n".join([f"• {stat.title()}: {level}" for stat, level in recommended_stats.items()]),
                        inline=True
                    )

                elif "slayer_info" in metadata["additional_info"]:
                    slayer_info = metadata["additional_info"]["slayer_info"]
                    embed.add_field(
                        name="Slayer Information",
                        value=f"Level Required: {slayer_info['requirement']}\nCategory: {slayer_info['category']}",
                        inline=True
                    )

        # Add combat information
        embed.add_field(
            name="Combat Info",
            value=f"Combat Level: {monster['combat_level']}\nHP: {monster['hitpoints']}\nMax Hit: {monster['max_hit']}\nAttack Speed: {monster['attack_speed']}",
            inline=True
        )

        # Add drops information
        notable_drops = []
        for item_id, drop_info in monster["drops"].items():
            if drop_info["chance"] < 0.1:  # Show rare drops
                item_name = item_id.replace("_", " ").title()
                chance_percent = drop_info["chance"] * 100
                notable_drops.append(f"• {item_name} ({chance_percent:.2f}%)")

        if notable_drops:
            embed.add_field(
                name="Notable Drops",
                value="\n".join(notable_drops),
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="attack")
    async def attack_command(self, interaction: discord.Interaction):
        """Attack the monster you're fighting"""
        character = await self.db.get_character(interaction.user.id)
        if not character:
            await interaction.response.send_message("You need to create a character first!")
            return

        result = self.combat_manager.process_attack(character["id"])
        if not result:
            await interaction.response.send_message("You're not in combat!")
            return

        monster = self.game_data.get_monster(result["monster_id"])
        monster_id = monster["name"].lower().replace(" ", "_")
        metadata = self.game_data.get_wiki_metadata("monsters", monster_id)

        embed = discord.Embed(
            title=f"Combat with {monster['name']}", 
            color=discord.Color.red()
        )

        if metadata:
            embed.set_thumbnail(url=metadata["image_url"])

        # Combat round information
        if result["player_damage"] > 0:
            embed.add_field(
                name="Your Attack",
                value=f"You hit the {monster['name']} for {result['player_damage']} damage!",
                inline=False
            )
        else:
            embed.add_field(
                name="Your Attack",
                value=f"You missed the {monster['name']}!",
                inline=False
            )

        if result["monster_damage"] > 0:
            embed.add_field(
                name="Monster Attack",
                value=f"The {monster['name']} hit you for {result['monster_damage']} damage!",
                inline=False
            )
        else:
            embed.add_field(
                name="Monster Attack",
                value=f"The {monster['name']} missed you!",
                inline=False
            )

        # Status
        embed.add_field(
            name="Status",
            value=f"Your HP: {result['player_hp']}\n{monster['name']}'s HP: {result['monster_hp']}",
            inline=False
        )

        if result["combat_ended"]:
            if result["victory"]:
                embed.add_field(
                    name="Victory!",
                    value=f"You defeated the {monster['name']}!",
                    inline=False
                )
                
                if result["drops"]:
                    drops_text = []
                    for item_id, amount in result["drops"].items():
                        item_name = item_id.replace("_", " ").title()
                        drops_text.append(f"• {item_name} x{amount}")
                    
                    embed.add_field(
                        name="Drops Received",
                        value="\n".join(drops_text),
                        inline=False
                    )

                if result["xp_gained"]:
                    xp_text = []
                    for skill, xp in result["xp_gained"].items():
                        xp_text.append(f"• {skill.title()}: {xp:,} xp")
                    
                    embed.add_field(
                        name="Experience Gained",
                        value="\n".join(xp_text),
                        inline=False
                    )
            else:
                embed.add_field(
                    name="Defeat",
                    value=f"You were defeated by the {monster['name']}!",
                    inline=False
                )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="flee")
    async def flee_command(self, interaction: discord.Interaction):
        """Attempt to flee from combat"""
        character = await self.db.get_character(interaction.user.id)
        if not character:
            await interaction.response.send_message("You need to create a character first!")
            return

        result = self.combat_manager.flee_fight(character["id"])
        if not result:
            await interaction.response.send_message("You're not in combat!")
            return

        monster = self.game_data.get_monster(result["monster_id"])
        monster_id = monster["name"].lower().replace(" ", "_")
        metadata = self.game_data.get_wiki_metadata("monsters", monster_id)

        embed = discord.Embed(
            title="Escape Attempt",
            color=discord.Color.yellow()
        )

        if metadata:
            embed.set_thumbnail(url=metadata["image_url"])

        if result["success"]:
            embed.description = f"You successfully fled from the {monster['name']}!"
        else:
            embed.description = f"You failed to flee from the {monster['name']}!"
            if result["damage_taken"] > 0:
                embed.add_field(
                    name="Damage Taken",
                    value=f"You took {result['damage_taken']} damage while trying to escape!",
                    inline=False
                )
            embed.add_field(
                name="Status",
                value=f"Your HP: {result['player_hp']}\n{monster['name']}'s HP: {result['monster_hp']}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    def calculate_combat_level(self, stats: CombatStats) -> int:
        """Calculate combat level using OSRS formula"""
        base = 0.25 * (
            stats["defence"] +
            stats["hitpoints"] +
            math.floor(stats["prayer"] / 2)
        )

        melee = 0.325 * (
            stats["attack"] +
            stats["strength"]
        )

        ranged = 0.325 * (
            math.floor(3 * stats["ranged"] / 2)
        )

        magic = 0.325 * (
            math.floor(3 * stats["magic"] / 2)
        )

        combat = base + max(melee, ranged, magic)
        return math.floor(combat)

    async def get_combat_stats(self, player_id: int) -> Optional[CombatStats]:
        """Get a player's combat stats from the database"""
        # TODO: Implement database retrieval
        return None

    async def set_attack_style(self, player_id: int, style: CombatStyle) -> bool:
        """Set a player's attack style"""
        # TODO: Implement database update
        return False

    async def get_prayer_points(self, player_id: int) -> int:
        """Get a player's prayer points"""
        # TODO: Implement database retrieval
        return 0

    async def set_prayer_status(self, player_id: int, prayer: str, enabled: bool) -> bool:
        """Set a prayer's active status"""
        # TODO: Implement database update
        return False

    async def get_special_attack_energy(self, player_id: int) -> int:
        """Get a player's special attack energy"""
        # TODO: Implement database retrieval
        return 0

    async def get_equipped_weapon(self, player_id: int) -> Optional[Dict]:
        """Get a player's equipped weapon"""
        # TODO: Implement database retrieval
        return None

    async def use_special_attack(self, player_id: int) -> bool:
        """Use special attack and reduce energy"""
        # TODO: Implement database update
        return False

    async def restore_combat_stats(self, player_id: int) -> bool:
        """Restore combat stats to base levels"""
        # TODO: Implement database update
        return False

    async def check_inventory(self, player_id: int, item: str) -> bool:
        """Check if player has an item in their inventory"""
        # TODO: Implement database check
        return False

    async def get_food_healing(self, food: str) -> Optional[int]:
        """Get healing amount for a food item"""
        # TODO: Implement food data lookup
        return None

    async def heal_player(self, player_id: int, amount: int) -> tuple[bool, int]:
        """Heal player and return success status and new HP"""
        # TODO: Implement database update
        return False, 0

    async def get_potion_effects(self, potion: str) -> Optional[Dict[str, int]]:
        """Get effects for a potion"""
        # TODO: Implement potion data lookup
        return None

    async def apply_potion(self, player_id: int, effects: Dict[str, int]) -> tuple[bool, Dict[str, int]]:
        """Apply potion effects and return success status and new stats"""
        # TODO: Implement database update
        return False, {}

async def setup(bot: commands.Bot):
    """Add the combat commands to the bot"""
    db = bot.get_cog("Database").db
    game_data = bot.get_cog("GameData").game_data
    await bot.add_cog(CombatCommands(bot, db, game_data)) 