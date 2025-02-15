import discord
from discord.ext import commands
import random
from typing import List, Dict

class FunCommands(commands.Cog):
    """A collection of fun commands for entertainment"""
    


    def __init__(self, bot):
        self.bot = bot
        # Move all constants here from main file
        self.NANI_RESPONSES = [
            "お前はもう死んでいる。\n*(Omae wa mou shindeiru)*\n**NANI?!** 💥",
            "*teleports behind you*\nNothing personal, kid... 🗡️",
            "このDIOだ!\n*(KONO DIO DA!)* 🧛‍♂️",
            "MUDA MUDA MUDA MUDA! 👊",
            "ROAD ROLLER DA! 🚛",
            "ゴゴゴゴ\n*(Menacing...)* ゴゴゴゴ",
            "やれやれだぜ...\n*(Yare yare daze...)* 🎭",
            "NANI?! BAKANA! MASAKA! 😱",
            "僕が来た!\n*(I AM HERE!)* 💪",
            "掛かって来い!\n*(Come at me!)* ⚔️"
        ]
        self.DOUBT_GIFS = [
            "https://tenor.com/view/doubt-press-x-la-noire-gif-11674382",
            "https://tenor.com/view/doubt-x-gif-19284783",
            "https://tenor.com/view/la-noire-doubt-x-to-doubt-cole-phelps-gif-22997643"
        ]

    @commands.command(name='hello')
    async def hello(self, ctx):
        """Basic greeting"""
        embed = discord.Embed(
            title="Hello! 👋",
            description="This is your friendly neighborhood Discord-Plex bot!",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Requested by {ctx.author.name}")
        await ctx.send(embed=embed)
        await ctx.message.add_reaction('👋')

    @commands.command(name='nani')
    async def nani(self, ctx):
        """NANI?! response"""
        embed = discord.Embed(
            title="⚡ NANI?! ⚡",
            description=random.choice(self.NANI_RESPONSES),
            color=discord.Color.red()
        )
        reactions = ['💥', '⚡', '🗡️', '👊', '😱']
        for reaction in reactions:
            await ctx.message.add_reaction(reaction)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FunCommands(bot))