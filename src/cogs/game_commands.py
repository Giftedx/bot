import asyncio
import random

import discord
from discord.ext import commands


class GameCommands(commands.Cog):
    """Gaming commands and mini-games manager"""

    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}
        self.WORDS = [
            "DISCORD",
            "PYTHON",
            "GAMING",
            "HANGMAN",
            "WIZARD",
            "PROGRAMMING",
            "JAVASCRIPT",
            "DEVELOPER",
            "COMPUTER",
        ]
        self.TRIVIA_CATEGORIES = {
            "gaming": "🎮 Gaming",
            "anime": "🎭 Anime",
            "coding": "💻 Programming",
            "general": "🌍 General Knowledge",
        }

    @commands.group(invoke_without_command=True)
    async def games(self, ctx):
        """📊 Game Categories:

        RPG Systems:
        🎮 OSRS (!osrs)
        • Character creation & stats
        • Skill training system
        • World navigation
        • Combat system

        🐾 Pokemon (!pokemon)
        • Catch & collect Pokemon
        • Battle other trainers
        • Train & evolve Pokemon
        • Manage your collection

        Mini-Games:
        📝 Word Games
        • !hangman - Classic word guessing
        • !wordle - Daily word puzzle
        • !wordchain - Word association

        🧠 Knowledge Games
        • !trivia [category] - Multi-category quiz
        • !quiz - General knowledge
        • !memory - Memory challenge

        🎲 Quick Games
        • !rps - Rock, Paper, Scissors
        • !dice [sides] - Roll dice
        • !flip - Coin flip
        • !8ball - Ask the magic 8-ball

        Use !help <game> for detailed instructions
        Example: !help pokemon"""

        embed = discord.Embed(
            title="🎮 Game Center",
            description="Welcome to the Game Center! Choose your adventure:",
            color=discord.Color.blue(),
        )

        # RPG Systems
        rpg_desc = """
        **!osrs** - Old School RuneScape Simulation
        • Create character, train skills, explore worlds

        **!pokemon** - Pokemon Adventure
        • Catch, battle, train, and evolve Pokemon
        """
        embed.add_field(name="🎯 RPG Systems", value=rpg_desc, inline=False)

        # Word Games
        word_desc = """
        **!hangman** - Classic word guessing game
        **!wordle** - Daily word puzzle challenge
        **!wordchain** - Word association game
        """
        embed.add_field(name="📝 Word Games", value=word_desc, inline=False)

        # Knowledge Games
        know_desc = """
        **!trivia [category]** - Multi-category quiz
        Available categories: gaming, anime, coding, general
        **!quiz** - General knowledge questions
        **!memory** - Test your memory
        """
        embed.add_field(name="🧠 Knowledge Games", value=know_desc, inline=False)

        # Quick Games
        quick_desc = """
        **!rps <choice>** - Rock, Paper, Scissors
        **!dice [sides]** - Roll dice (default: d20)
        **!flip** - Flip a coin
        **!8ball <question>** - Ask the magic 8-ball
        """
        embed.add_field(name="🎲 Quick Games", value=quick_desc, inline=False)

        embed.set_footer(text="Type !help <game> for detailed instructions on any game!")
        await ctx.send(embed=embed)

    # Word Games
    @commands.command()
    async def hangman(self, ctx):
        """🎯 Classic Hangman Word Game

        How to Play:
        1. Start game with !hangman
        2. Guess one letter at a time
        3. You have 6 tries to guess the word
        4. Game shows:
           • Word progress (e.g., H _ L L _)
           • Letters guessed
           • Tries remaining
           • Hangman drawing

        Win: Guess the word before the hangman is complete
        Lose: Run out of tries (6 wrong guesses)

        Tips:
        • Start with common letters (E, A, R, I, O)
        • Watch others' guesses in multiplayer
        • Use letter patterns to guess words
        """
        if ctx.channel.id in self.active_games:
            await ctx.send("A game is already active in this channel!")
            return

        word = random.choice(self.WORDS)
        guessed = set()
        tries_left = 6

        # ... rest of hangman implementation ...

    @commands.command()
    async def wordle(self, ctx):
        """🎯 Daily Word Puzzle (Wordle)

        How to Play:
        1. Guess the 5-letter word
        2. Colors show hint for each letter:
           🟩 Green = Right letter, right spot
           🟨 Yellow = Right letter, wrong spot
           ⬛ Black = Letter not in word
        3. Six tries to guess the word
        4. One game per day per user

        Tips:
        • Start with words using common letters
        • Use letter hints from previous guesses
        • Track which letters you've tried
        """
        # ... wordle implementation ...

    # Knowledge Games
    @commands.command()
    async def trivia(self, ctx, category: str = "random"):
        """🧠 Multi-Category Trivia Game

        Categories:
        • gaming - Video games & gaming culture
        • anime - Anime & manga knowledge
        • coding - Programming & tech
        • general - General knowledge
        • random - Mix of all categories

        How to Play:
        1. Select category (optional)
        2. Answer questions within 30 seconds
        3. First correct answer wins
        4. Points awarded for correct answers

        Usage: !trivia [category]
        Example: !trivia gaming
        """
        category = category.lower()
        if category not in self.TRIVIA_CATEGORIES:
            categories = ", ".join(self.TRIVIA_CATEGORIES.keys())
            await ctx.send(f"Invalid category! Choose from: {categories}")
            return

        # ... rest of trivia implementation ...

    # Quick Games
    @commands.command()
    async def rps(self, ctx, choice: str = None):
        """🎲 Rock Paper Scissors

        How to Play:
        1. Type !rps <choice>
        2. Choose: rock, paper, or scissors
        3. Bot makes its choice
        4. Winner determined by classic rules:
           • Rock crushes Scissors
           • Scissors cuts Paper
           • Paper covers Rock

        Usage: !rps <choice>
        Example: !rps rock
        """
        choices = ["rock", "paper", "scissors"]
        if not choice or choice.lower() not in choices:
            await ctx.send("Please choose rock, paper, or scissors!")
            return

        # ... rest of RPS implementation ...

    @commands.command()
    async def dice(self, ctx, sides: int = 20):
        """🎲 Roll Dice

        Roll a dice with custom sides
        Default is d20 (20-sided dice)

        Options:
        • Standard dice: 4, 6, 8, 10, 12, 20, 100
        • Custom sides: 1-100

        Usage: !dice [sides]
        Example: !dice 6
        """
        if sides < 1 or sides > 100:
            await ctx.send("Please choose between 1 and 100 sides!")
            return

        result = random.randint(1, sides)
        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"Rolling d{sides}...\n\nResult: **{result}**",
            color=discord.Color.blue(),
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def flip(self, ctx):
        """🎲 Flip a Coin

        Flip a coin to get heads or tails
        Animated coin flip with result

        Usage: !flip
        """
        choices = ["Heads", "Tails"]
        result = random.choice(choices)
        embed = discord.Embed(
            title="🪙 Coin Flip", description="Flipping...", color=discord.Color.gold()
        )
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(1)
        embed.description = f"Result: **{result}**! {'⚪' if result == 'Heads' else '⚫'}"
        await msg.edit(embed=embed)


async def setup(bot):
    await bot.add_cog(GameCommands(bot))
