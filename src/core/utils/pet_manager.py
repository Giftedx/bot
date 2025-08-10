from typing import Dict, List, Optional
from discord.ext import commands
import discord
from datetime import datetime

from src.core.pet_system import Pet, PetManager, PetOrigin, PetRarity


class PetManagerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pet_manager = PetManager()

    @commands.group(invoke_without_command=True)
    async def pets(self, ctx):
        """Display all pets owned by the user"""
        pets = self.pet_manager.get_pets_by_owner(ctx.author.id)

        if not pets:
            await ctx.send(
                "You don't have any pets yet! Try getting some from OSRS activities or Pokemon encounters!"
            )
            return

        # Group pets by origin
        pets_by_origin: Dict[PetOrigin, List[Pet]] = {
            PetOrigin.OSRS: [],
            PetOrigin.POKEMON: [],
            PetOrigin.CUSTOM: [],
        }

        for pet in pets:
            pets_by_origin[pet.origin].append(pet)

        embed = discord.Embed(
            title="🐾 Your Pet Collection",
            description=f"You have {len(pets)} pets in total!",
            color=discord.Color.gold(),
        )

        for origin, pet_list in pets_by_origin.items():
            if pet_list:
                pet_count = len(pet_list)
                rarest_pet = max(pet_list, key=lambda p: p.rarity.value)
                highest_level = max(pet_list, key=lambda p: p.stats.level)

                value = (
                    f"Total: {pet_count}\n"
                    f"Rarest: {rarest_pet.name} ({rarest_pet.rarity.name})\n"
                    f"Highest Level: {highest_level.name} (Level {highest_level.stats.level})"
                )

                embed.add_field(name=f"{origin.value.title()} Pets", value=value, inline=False)

        await ctx.send(embed=embed)

    @pets.command(name="interact")
    async def pet_interact(self, ctx, pet_name: str):
        """Interact with any of your pets"""
        pets = self.pet_manager.get_pets_by_owner(ctx.author.id)
        matching_pets = [p for p in pets if p.name.lower() == pet_name.lower()]

        if not matching_pets:
            await ctx.send(f"You don't have a pet named {pet_name}!")
            return

        pet = matching_pets[0]
        interaction_result = pet.interact("play")

        embed = discord.Embed(
            title="🤗 Pet Interaction",
            description=f"You spent some time with {pet.name}!",
            color=discord.Color.green(),
        )

        embed.add_field(name="Experience Gained", value=interaction_result["exp_gained"])
        embed.add_field(name="Happiness Gained", value=interaction_result["happiness_gained"])
        if interaction_result["leveled_up"]:
            embed.add_field(
                name="Level Up!",
                value=f"{pet.name} grew to level {interaction_result['current_level']}! 🎉",
                inline=False,
            )

        await ctx.send(embed=embed)

    @pets.command(name="info")
    async def pet_info(self, ctx, pet_name: str):
        """Get detailed information about a specific pet"""
        pets = self.pet_manager.get_pets_by_owner(ctx.author.id)
        matching_pets = [p for p in pets if p.name.lower() == pet_name.lower()]

        if not matching_pets:
            await ctx.send(f"You don't have a pet named {pet_name}!")
            return

        pet = matching_pets[0]

        embed = discord.Embed(
            title=f"🔍 {pet.name} Info",
            description=f"Origin: {pet.origin.value.title()}",
            color=discord.Color.blue(),
        )

        # Basic Stats
        embed.add_field(
            name="Stats",
            value=(
                f"Level: {pet.stats.level}\n"
                f"Experience: {pet.stats.experience}\n"
                f"Happiness: {pet.stats.happiness}/100\n"
                f"Loyalty: {pet.stats.loyalty}"
            ),
            inline=False,
        )

        # Base Stats
        base_stats = "\n".join(f"{stat}: {value}" for stat, value in pet.base_stats.items())
        embed.add_field(name="Base Stats", value=base_stats, inline=False)

        # Abilities
        embed.add_field(name="Abilities", value=", ".join(pet.abilities), inline=False)

        # Additional Info based on origin
        if pet.origin == PetOrigin.POKEMON:
            embed.add_field(name="Type", value=" / ".join(pet.metadata["type"]), inline=False)
        elif pet.origin == PetOrigin.OSRS:
            if "boss" in pet.metadata:
                embed.add_field(name="Boss", value=pet.metadata["boss"], inline=False)
            elif "skill" in pet.metadata:
                embed.add_field(name="Skill", value=pet.metadata["skill"], inline=False)

        # Time owned
        time_owned = datetime.now() - pet.obtained_date
        days_owned = time_owned.days
        embed.add_field(name="Time Owned", value=f"{days_owned} days", inline=False)

        await ctx.send(embed=embed)

    @pets.command(name="leaderboard")
    async def pet_leaderboard(self, ctx):
        """Display the server's pet leaderboard"""
        all_pets = self.pet_manager.pets.values()
        if not all_pets:
            await ctx.send("No pets have been registered yet!")
            return

        # Get unique pet owners
        pet_owners = set(pet.owner_id for pet in all_pets)

        # Calculate scores for each owner
        owner_scores = []
        for owner_id in pet_owners:
            owner_pets = [p for p in all_pets if p.owner_id == owner_id]
            score = sum(p.rarity.value * p.stats.level for p in owner_pets)
            owner_scores.append((owner_id, score, len(owner_pets)))

        # Sort by score
        owner_scores.sort(key=lambda x: x[1], reverse=True)

        embed = discord.Embed(
            title="🏆 Pet Leaderboard", description="Top Pet Collectors", color=discord.Color.gold()
        )

        for i, (owner_id, score, pet_count) in enumerate(owner_scores[:10], 1):
            member = ctx.guild.get_member(owner_id)
            if member:
                name = member.display_name
                value = f"Score: {score:,}\nPets: {pet_count}"
                embed.add_field(name=f"{i}. {name}", value=value, inline=False)

        await ctx.send(embed=embed)

    @pets.command(name="search")
    async def pet_search(self, ctx, rarity: Optional[str] = None, origin: Optional[str] = None):
        """Search for pets by rarity and/or origin"""
        pets = self.pet_manager.get_pets_by_owner(ctx.author.id)

        # Filter by rarity if specified
        if rarity:
            try:
                rarity_enum = PetRarity[rarity.upper()]
                pets = [p for p in pets if p.rarity == rarity_enum]
            except KeyError:
                await ctx.send(
                    f"Invalid rarity! Choose from: {', '.join(r.name for r in PetRarity)}"
                )
                return

        # Filter by origin if specified
        if origin:
            try:
                origin_enum = PetOrigin[origin.upper()]
                pets = [p for p in pets if p.origin == origin_enum]
            except KeyError:
                await ctx.send(
                    f"Invalid origin! Choose from: {', '.join(o.name for o in PetOrigin)}"
                )
                return

        if not pets:
            await ctx.send("No pets found matching your search criteria!")
            return

        embed = discord.Embed(
            title="🔍 Pet Search Results",
            description=f"Found {len(pets)} pets matching your criteria!",
            color=discord.Color.blue(),
        )

        for pet in pets:
            pet_info = (
                f"Origin: {pet.origin.value.title()}\n"
                f"Rarity: {pet.rarity.name}\n"
                f"Level: {pet.stats.level}"
            )
            embed.add_field(name=pet.name, value=pet_info, inline=False)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(PetManagerCog(bot))
