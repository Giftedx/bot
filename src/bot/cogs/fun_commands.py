import discord
from discord.ext import commands
import random

class FunCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='hello')
    async def hello(self, ctx):
        """Basic greeting"""
        await ctx.send(f"Hello {ctx.author.name}! 👋")

    @commands.command(name='wizard')
    async def wizard(self, ctx):
        """Magical greeting"""
        spells = [
            "*Wingardium Leviosa!* `(Your messages float up)` ⬆️",
            "*Lumos!* `(The chat brightens)` 💡",
            "*Expecto Patronum!* `(A spirit animal appears)` 🦌",
            "*Alohomora!* `(Unlocks hidden channels)` 🔓",
            "*Riddikulus!* `(Turns fear into laughter)` 😂"
        ]
        await ctx.send(random.choice(spells))

    # Add more fun commands here...

async def setup(bot):
    await bot.add_cog(FunCommands(bot))