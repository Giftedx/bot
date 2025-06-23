from discord.ext import commands
from discord import Embed, Color
import random
from typing import Optional
from datetime import datetime

from .pet_manager import PetManager
from ..osrs.osrs_pet import OSRSPet
from ..pokemon.pokemon_pet import PokemonPet
from ...config.game_config import game_config, PetType, Rarity
from ...config.achievements import achievement_config, AchievementType
from .event_system import EventManager, EventType, GameEvent, SpecialEventHandler
from .achievement_manager import AchievementManager
from ...database.db_service import DatabaseService


class PetCommands(commands.Cog):
    def __init__(self, bot, db_url: str):
        self.bot = bot
        self.pet_manager = PetManager()
        self.event_manager = EventManager()
        self.db_service = DatabaseService(db_url)
        self.special_handler = SpecialEventHandler(self.db_service)
        self.achievement_manager = AchievementManager(self.db_service, self.event_manager)

    @commands.group(invoke_without_command=True)
    async def pet(self, ctx):
        """Base pet command. Shows pet help if no subcommand is given."""
        embed = Embed(title="Pet System Commands", color=Color.blue())
        embed.add_field(
            name="Get a Pet",
            value="`!pet catch [pokemon/osrs]` - Try to get a new pet",
            inline=False,
        )
        embed.add_field(name="View Pets", value="`!pet list` - View your pets", inline=False)
        embed.add_field(
            name="Pet Stats", value="`!pet stats` - View your pet statistics", inline=False
        )
        embed.add_field(
            name="Train Pet", value="`!pet train <pet_id>` - Train your pet", inline=False
        )
        embed.add_field(
            name="View Boosts", value="`!pet boosts` - View your active boosts", inline=False
        )
        embed.add_field(
            name="Achievements", value="`!pet achievements` - View your achievements", inline=False
        )
        embed.add_field(
            name="Achievement Progress",
            value="`!pet progress` - Check achievement progress",
            inline=False,
        )
        await ctx.send(embed=embed)

    @pet.command()
    async def catch(self, ctx, pet_type_str: str):
        """Try to catch/obtain a new pet"""
        try:
            pet_type = PetType(pet_type_str.lower())
        except ValueError:
            await ctx.send("Invalid pet type! Choose 'pokemon' or 'osrs'")
            return

        # Get active boosts from database
        active_boosts = self.db_service.get_active_boosts(str(ctx.author.id))
        total_boost = sum(
            boost.boost_value for boost in active_boosts if boost.target_type == pet_type.value
        )

        config = game_config.get_pet_config(pet_type)
        base_chance = config.base_catch_rate
        final_chance = min(base_chance + total_boost, config.max_boost)

        if random.random() > final_chance:
            await ctx.send("No pet found this time! Keep trying!")
            return

        try:
            if pet_type == PetType.OSRS:
                # Get random pet from configuration
                pet_name, pet_data = random.choice(list(config.pets.items()))
                pet = self.pet_manager.add_pet(
                    str(ctx.author.id),
                    "osrs",
                    name=pet_name,
                    pet_type=pet_name,
                    rarity=pet_data["rarity"].value,
                )

            elif pet_type == PetType.POKEMON:
                # Get random species from configuration
                species, species_data = random.choice(list(config.species.items()))
                pet = self.pet_manager.add_pet(
                    str(ctx.author.id),
                    "pokemon",
                    name=species,
                    species=species,
                    rarity=species_data["rarity"].value,
                )

            # Save to database
            self.db_service.add_pet(str(ctx.author.id), pet.to_dict())

            # Emit pet obtained event
            self.event_manager.emit(
                GameEvent(
                    type=EventType.PET_OBTAINED,
                    user_id=str(ctx.author.id),
                    timestamp=datetime.utcnow(),
                    data={"pet_type": pet_type.value, "pet_id": pet.pet_id, "rarity": pet.rarity},
                )
            )

            embed = Embed(title="New Pet!", color=Color.green())
            embed.add_field(name="Type", value=pet_type.value.upper())
            embed.add_field(name="Name", value=pet.name)
            embed.add_field(name="Rarity", value=pet.rarity.upper())
            embed.add_field(name="Special Ability", value=pet.special_ability())
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error getting pet: {str(e)}")

    @pet.command()
    async def train(self, ctx, pet_id: str):
        """Train a specific pet"""
        pet = self.pet_manager.get_pet(pet_id)

        if not pet:
            await ctx.send("Pet not found!")
            return

        if str(ctx.author.id) != pet.owner_id:
            await ctx.send("This isn't your pet!")
            return

        config = game_config.get_pet_config(PetType(pet.pet_type))

        if isinstance(pet, OSRSPet):
            if pet.level >= config.max_level:
                await ctx.send(f"{pet.name} has reached the maximum level!")
                return

            pet.level_combat()
            exp_range = config.boss_exp_range
            exp_gained = random.randint(exp_range[0], exp_range[1])
            pet.gain_experience(exp_gained)

            # Emit boss kill event if applicable
            if pet.kill_count > 0 and pet.kill_count % 100 == 0:
                self.event_manager.emit(
                    GameEvent(
                        type=EventType.OSRS_BOSS_KILLED,
                        user_id=str(ctx.author.id),
                        timestamp=datetime.utcnow(),
                        data={"kill_count": pet.kill_count},
                    )
                )

            await ctx.send(
                f"{pet.name} gained {exp_gained} XP and improved their combat level to {pet.combat_level}!"
            )

        elif isinstance(pet, PokemonPet):
            if pet.level >= config.max_level:
                await ctx.send(f"{pet.name} has reached the maximum level!")
                return

            # Random move learning during training
            species_data = config.species.get(pet.species, {})
            possible_moves = species_data.get("possible_moves", [])

            if possible_moves and random.random() < config.move_learn_chance:
                new_move = random.choice(possible_moves)
                if pet.learn_move(new_move):
                    await ctx.send(f"{pet.name} learned {new_move}!")

            exp_gained = random.randint(30, 60)
            pet.gain_experience(exp_gained)
            await ctx.send(f"{pet.name} gained {exp_gained} XP!")

            # Check for evolution
            if pet.check_evolution():
                evolution = species_data.get("evolution")
                if evolution:
                    pet.evolve(evolution)
                    await ctx.send(f"Congratulations! Your {pet.name} evolved into {evolution}!")

                    # Emit evolution event
                    self.event_manager.emit(
                        GameEvent(
                            type=EventType.POKEMON_EVOLVED,
                            user_id=str(ctx.author.id),
                            timestamp=datetime.utcnow(),
                            data={"original_species": pet.species, "evolved_species": evolution},
                        )
                    )

        # Update pet in database
        self.db_service.update_pet(pet_id, pet.to_dict())

    @pet.command()
    async def boosts(self, ctx):
        """View active boosts"""
        active_boosts = self.db_service.get_active_boosts(str(ctx.author.id))

        if not active_boosts:
            await ctx.send("You have no active boosts!")
            return

        embed = Embed(title="Active Boosts", color=Color.gold())
        for boost in active_boosts:
            embed.add_field(
                name=f"{boost.source_type.upper()} → {boost.target_type.upper()}",
                value=f"Boost: +{boost.boost_value:.1%}\n"
                + (f"Expires: {boost.expires_at}" if boost.expires_at else "Permanent"),
                inline=False,
            )

        await ctx.send(embed=embed)

    @pet.command()
    async def stats(self, ctx):
        """View pet statistics"""
        stats = self.pet_manager.get_pet_stats(str(ctx.author.id))
        active_boosts = self.db_service.get_active_boosts(str(ctx.author.id))

        embed = Embed(title="Pet Statistics", color=Color.gold())
        embed.add_field(name="Total Pets", value=stats["total_pets"])
        embed.add_field(name="Average Level", value=f"{stats['average_level']:.1f}")
        embed.add_field(name="Highest Level", value=stats["highest_level"])
        embed.add_field(name="OSRS Pets", value=stats["pet_types"]["osrs"])
        embed.add_field(name="Pokemon", value=stats["pet_types"]["pokemon"])

        # Show active boosts
        boost_text = ""
        for boost in active_boosts:
            boost_text += f"{boost.source_type} → {boost.target_type}: +{boost.boost_value:.1%}\n"

        if boost_text:
            embed.add_field(name="Active Boosts", value=boost_text, inline=False)

        await ctx.send(embed=embed)

    @pet.command()
    async def achievements(self, ctx):
        """View completed achievements"""
        achievements = await self.achievement_manager.get_user_achievements(str(ctx.author.id))

        if not achievements:
            await ctx.send("You haven't earned any achievements yet! Keep training your pets!")
            return

        embed = Embed(title="Your Achievements", color=Color.gold())

        # Group achievements by type
        by_type = {}
        for ach in achievements:
            ach_type = ach["type"]
            if ach_type not in by_type:
                by_type[ach_type] = []
            by_type[ach_type].append(ach)

        for ach_type, type_achievements in by_type.items():
            achievements_text = ""
            for ach in type_achievements:
                config_ach = achievement_config.get_achievement(ach["id"])
                if config_ach:
                    achievements_text += f"{config_ach.icon} **{ach['name']}**\n"
                    if "title" in ach["rewards"]:
                        achievements_text += f"Title: {ach['rewards']['title']}\n"
                    achievements_text += f"Awarded: {ach['awarded_at']}\n\n"

            if achievements_text:
                embed.add_field(
                    name=f"{ach_type.title()} Achievements", value=achievements_text, inline=False
                )

        await ctx.send(embed=embed)

    @pet.command()
    async def progress(self, ctx):
        """Check achievement progress"""
        progress = await self.achievement_manager.get_achievement_progress(str(ctx.author.id))

        embed = Embed(title="Achievement Progress", color=Color.blue())

        # Group by achievement type
        by_type = {}
        for ach_id, prog in progress.items():
            ach = prog["achievement"]
            if ach.type not in by_type:
                by_type[ach.type] = []
            by_type[ach.type].append((ach, prog))

        for ach_type, type_progress in by_type.items():
            progress_text = ""
            for ach, prog in type_progress:
                status = "✅" if prog["completed"] else "🔄"
                progress_text += f"{ach.icon} **{ach.name}** {status}\n"
                progress_text += f"Progress: {prog['progress']:.1f}%\n"
                progress_text += f"{ach.description}\n\n"

            if progress_text:
                embed.add_field(
                    name=f"{ach_type.value.title()} Achievements", value=progress_text, inline=False
                )

        await ctx.send(embed=embed)

    @pet.command()
    async def title(self, ctx, *, title_id: str = None):
        """Set or view available titles"""
        if title_id is None:
            # Show available titles
            achievements = await self.achievement_manager.get_user_achievements(str(ctx.author.id))
            titles = []
            for ach in achievements:
                if "title" in ach["rewards"]:
                    titles.append(
                        {
                            "id": ach["id"],
                            "title": ach["rewards"]["title"],
                            "achievement": ach["name"],
                        }
                    )

            if not titles:
                await ctx.send(
                    "You haven't earned any titles yet! Complete achievements to earn titles!"
                )
                return

            embed = Embed(title="Your Available Titles", color=Color.blue())
            for title_info in titles:
                embed.add_field(
                    name=title_info["title"],
                    value=f"From: {title_info['achievement']}\nUse: `!pet title {title_info['id']}`",
                    inline=False,
                )

            await ctx.send(embed=embed)
        else:
            # Set title
            achievements = await self.achievement_manager.get_user_achievements(str(ctx.author.id))
            for ach in achievements:
                if ach["id"] == title_id and "title" in ach["rewards"]:
                    await self.db_service.set_user_title(
                        str(ctx.author.id), ach["rewards"]["title"]
                    )
                    await ctx.send(f"Title set to: {ach['rewards']['title']}")
                    return

            await ctx.send("Title not found or not earned!")


async def setup(bot):
    await bot.add_cog(PetCommands(bot, "your_database_url_here"))
