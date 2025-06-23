import discord
from discord.ext import commands
from discord import app_commands
import logging

from src.core.database import DatabaseManager
from src.core.battle_system import BattleManager, BattleResult, BattleType

logger = logging.getLogger(__name__)

class PetCommands(commands.Cog):
    """Commands for interacting with pets (hybrid: classic and slash)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_manager: DatabaseManager = self.bot.db_manager
        self.battle_manager: BattleManager = self.bot.battle_manager

    @commands.hybrid_command(name="pets", help="Lists your pets.")
    async def pets(self, ctx: commands.Context):
        """Lists the pets owned by the user."""
        try:
            player_id = str(ctx.author.id)
            pets = self.db_manager.get_player_pets(player_id)

            if not pets:
                await ctx.send("You don't have any pets yet!")
                return

            embed = discord.Embed(
                title=f"{ctx.author.name}'s Pets",
                color=discord.Color.green()
            )

            for pet in pets:
                pet_name = pet.get('name', 'Unnamed Pet')
                pet_type = pet.get('type', 'Unknown Type')
                pet_data = pet.get('data', {})
                level = pet_data.get('level', 1)
                embed.add_field(
                    name=f"**{pet_name}**",
                    value=f"Type: {pet_type}\nLevel: {level}",
                    inline=False
                )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in pets command: {e}", exc_info=True)
            await ctx.send("An error occurred while fetching your pets.")

    @commands.hybrid_command(name="battle", help="Battle another user's pet! Usage: /battle @user")
    @app_commands.describe(opponent="The user you want to battle")
    async def battle(self, ctx: commands.Context, opponent: discord.Member):
        """Initiates a pet battle with another user."""
        challenger = ctx.author

        if challenger.id == opponent.id:
            await ctx.send("You can't battle yourself!")
            return

        challenger_pets = self.db_manager.get_player_pets(str(challenger.id))
        opponent_pets = self.db_manager.get_player_pets(str(opponent.id))

        if not challenger_pets:
            await ctx.send("You don't have a pet to battle with!")
            return
        if not opponent_pets:
            await ctx.send(f"{opponent.name} doesn't have any pets to battle!")
            return

        # For simplicity, we'll use the first pet of each player
        challenger_pet = challenger_pets[0]
        opponent_pet = opponent_pets[0]
        await ctx.send(f"A battle is starting between {challenger.name}'s **{challenger_pet.name}** and {opponent.name}'s **{opponent_pet.name}**!")

        try:
            battle_id = self.battle_manager.create_battle(challenger_pet, opponent_pet, BattleType.PET)
            result: BattleResult = self.battle_manager.execute_battle(battle_id)

            if not result:
                await ctx.send("The battle could not be completed.")
                return

            winner = result.winner
            loser = result.loser
            # Persist changes
            self.db_manager.save_pet(winner)
            self.db_manager.save_pet(loser)

            embed = discord.Embed(
                title=f"Battle Over! {winner.name} is victorious!",
                description=f"The battle lasted {result.rounds} rounds.",
                color=discord.Color.gold()
            )
            embed.add_field(name="Winner", value=f"{winner.name} (Owner: <@{winner.owner_id}>)", inline=False)
            embed.add_field(name="Experience Gained", value=f"{result.exp_gained} XP", inline=True)
            embed.add_field(name="Loser", value=f"{loser.name} (Owner: <@{loser.owner_id}>)", inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"An error occurred during battle: {e}")
            await ctx.send("An unexpected error occurred during the battle.")

    @commands.hybrid_command(name="adopt", help="Adopt a new pet. Usage: /adopt <type> <name>")
    @app_commands.describe(pet_type="Type of pet to adopt (dog, cat, dragon, phoenix, unicorn)", name="Name for your new pet")
    async def adopt(self, ctx: commands.Context, pet_type: str, name: str):
        """Adopt a new pet with the given type and name."""
        pet_type = pet_type.lower()
        valid_types = ["dog", "cat", "dragon", "phoenix", "unicorn"]
        if pet_type not in valid_types:
            await ctx.send(f"Invalid pet type! Choose from: {', '.join(valid_types)}")
            return
        player_id = str(ctx.author.id)
        # Check for duplicate name
        pets = self.db_manager.get_player_pets(player_id)
        if any(p.get('name', '').lower() == name.lower() for p in pets):
            await ctx.send(f"You already have a pet named {name}!")
            return
        # Create pet data
        pet_data = {
            'name': name,
            'type': pet_type,
            'data': {'level': 1, 'experience': 0, 'happiness': 100},
            'owner_id': player_id
        }
        self.db_manager.save_pet(pet_data)
        embed = discord.Embed(
            title="🎉 New Pet Adopted!",
            description=f"Welcome {name} the {pet_type.title()} to your family!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="info", help="View detailed information about one of your pets. Usage: /info <name>")
    @app_commands.describe(name="Name of your pet")
    async def info(self, ctx: commands.Context, name: str):
        """View detailed information about your pet by name."""
        player_id = str(ctx.author.id)
        pets = self.db_manager.get_player_pets(player_id)
        pet = next((p for p in pets if p.get('name', '').lower() == name.lower()), None)
        if not pet:
            await ctx.send(f"You don't have a pet named {name}!")
            return
        pet_data = pet.get('data', {})
        embed = discord.Embed(
            title=f"{pet.get('name', 'Unnamed Pet')}'s Info",
            color=discord.Color.blue()
        )
        embed.add_field(name="Type", value=pet.get('type', 'Unknown'), inline=True)
        embed.add_field(name="Level", value=pet_data.get('level', 1), inline=True)
        embed.add_field(name="Experience", value=pet_data.get('experience', 0), inline=True)
        embed.add_field(name="Happiness", value=pet_data.get('happiness', 100), inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="train", help="Train one of your pets. Usage: /train <name>")
    @app_commands.describe(name="Name of your pet to train")
    async def train(self, ctx: commands.Context, name: str):
        """Train your pet to gain experience and possibly level up."""
        player_id = str(ctx.author.id)
        pets = self.db_manager.get_player_pets(player_id)
        pet = next((p for p in pets if p.get('name', '').lower() == name.lower()), None)
        if not pet:
            await ctx.send(f"You don't have a pet named {name}!")
            return
        pet_data = pet.get('data', {})
        # Simulate training: gain experience, possibly level up
        exp_gain = 20
        pet_data['experience'] = pet_data.get('experience', 0) + exp_gain
        old_level = pet_data.get('level', 1)
        new_level = 1 + (pet_data['experience'] // 100)
        leveled_up = new_level > old_level
        pet_data['level'] = new_level
        pet['data'] = pet_data
        self.db_manager.save_pet(pet)
        embed = discord.Embed(
            title=f"Training {pet.get('name', 'Unnamed Pet')}",
            description=f"Gained {exp_gain} XP!",
            color=discord.Color.blue()
        )
        embed.add_field(name="Level", value=new_level, inline=True)
        embed.add_field(name="Experience", value=pet_data['experience'], inline=True)
        if leveled_up:
            embed.add_field(name="Level Up!", value=f"{pet.get('name', 'Unnamed Pet')} leveled up to {new_level}! 🎉", inline=False)
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(PetCommands(bot)) 