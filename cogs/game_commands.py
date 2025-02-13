import discord
from discord.ext import commands
import random
from datetime import datetime, timedelta

class GameCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}

    @commands.hybrid_command()
    async def hangman(self, ctx: commands.Context):
        """Start a game of hangman"""
        if ctx.channel.id in self.active_games:
            await ctx.send("A game is already active in this channel!")
            return

        WORDS = [
            "DISCORD", "PYTHON", "GAMING", "HANGMAN", "WIZARD", 
            "PROGRAMMING", "JAVASCRIPT", "DEVELOPER", "COMPUTER"
        ]
        
        word = random.choice(WORDS)
        guessed = set()
        tries_left = 6
        HANGMAN_STAGES = [
            "```\n   +---+\n       |\n       |\n       |\n      ===```",
            "```\n   +---+\n   O   |\n       |\n       |\n      ===```",
            "```\n   +---+\n   O   |\n   |   |\n       |\n      ===```",
            "```\n   +---+\n   O   |\n  /|   |\n       |\n      ===```",
            "```\n   +---+\n   O   |\n  /|\\  |\n       |\n      ===```",
            "```\n   +---+\n   O   |\n  /|\\  |\n  /    |\n      ===```",
            "```\n   +---+\n   O   |\n  /|\\  |\n  / \\  |\n      ===```"
        ]

        def get_display_word():
            return " ".join(letter if letter in guessed else "_" for letter in word)

        embed = discord.Embed(
            title="🎯 Hangman Game",
            description=f"{HANGMAN_STAGES[6-tries_left]}\nWord: `{get_display_word()}`\nGuessed: {', '.join(sorted(guessed)) if guessed else 'None'}",
            color=discord.Color.blue()
        )
        
        game_message = await ctx.send(embed=embed)
        self.active_games[ctx.channel.id] = {
            "word": word,
            "message": game_message,
            "guessed": guessed,
            "tries": tries_left
        }

        def check(m):
            return (m.channel == ctx.channel and 
                   len(m.content) == 1 and 
                   m.content.isalpha())

        while tries_left > 0 and "_" in get_display_word():
            try:
                guess = await self.bot.wait_for('message', timeout=30.0, check=check)
                letter = guess.content.upper()

                if letter in guessed:
                    await ctx.send("You already guessed that letter!", delete_after=5)
                    continue

                guessed.add(letter)

                if letter in word:
                    if set(word) <= guessed:
                        await ctx.send(f"🎉 You won! The word was **{word}**")
                        break
                else:
                    tries_left -= 1
                    if tries_left == 0:
                        await ctx.send(f"💀 Game Over! The word was **{word}**")
                        break

                embed.description = f"{HANGMAN_STAGES[6-tries_left]}\nWord: `{get_display_word()}`\nGuessed: {', '.join(sorted(guessed))}"
                await game_message.edit(embed=embed)

            except TimeoutError:
                await ctx.send("Game timed out! ⏰")
                break

        del self.active_games[ctx.channel.id]

async def setup(bot):
    await bot.add_cog(GameCommands(bot))