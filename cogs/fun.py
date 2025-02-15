from discord.ext import commands
import discord
import random
import asyncio
from typing import Dict, List, Optional

class FunCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.marriages = {}
        self.pet_cooldowns = {}

    @commands.command()
    async def hug(self, ctx, member: discord.Member):
        """Hug someone"""
        hug_gifs = [
            "https://media.giphy.com/media/od5H3PmEG5EVq/giphy.gif",
            "https://media.giphy.com/media/3M4NpbLCTxBqU/giphy.gif",
            "https://media.giphy.com/media/PHZ7v9tfQu0o0/giphy.gif"
        ]
        embed = discord.Embed(
            description=f"{ctx.author.mention} hugs {member.mention} 🤗",
            color=discord.Color.pink()
        )
        embed.set_image(url=random.choice(hug_gifs))
        await ctx.send(embed=embed)

    @commands.command()
    async def pat(self, ctx, member: discord.Member):
        """Pat someone"""
        pat_gifs = [
            "https://media.giphy.com/media/5tmRHwTlHAA9WkVxTU/giphy.gif",
            "https://media.giphy.com/media/N0CIxcyPLputW/giphy.gif",
            "https://media.giphy.com/media/109ltuoSQT212w/giphy.gif"
        ]
        embed = discord.Embed(
            description=f"{ctx.author.mention} pats {member.mention} 🤚",
            color=discord.Color.blue()
        )
        embed.set_image(url=random.choice(pat_gifs))
        await ctx.send(embed=embed)

    @commands.command()
    async def marry(self, ctx, member: discord.Member):
        """Propose marriage to someone"""
        if ctx.author.id in self.marriages or member.id in self.marriages:
            return await ctx.send("One of you is already married!")

        await ctx.send(f"{member.mention}, do you accept {ctx.author.mention}'s proposal? (yes/no)")

        def check(m):
            return m.author == member and m.channel == ctx.channel and \
                   m.content.lower() in ['yes', 'no']

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30.0)
            if msg.content.lower() == 'yes':
                self.marriages[ctx.author.id] = member.id
                self.marriages[member.id] = ctx.author.id
                await ctx.send(f"💕 {ctx.author.mention} and {member.mention} are now married! 💕")
            else:
                await ctx.send("💔 The proposal was declined...")
        except asyncio.TimeoutError:
            await ctx.send("No response received, proposal cancelled.")

    @commands.command()
    async def divorce(self, ctx):
        """Divorce your partner"""
        if ctx.author.id not in self.marriages:
            return await ctx.send("You're not married!")

        partner_id = self.marriages[ctx.author.id]
        del self.marriages[ctx.author.id]
        del self.marriages[partner_id]
        await ctx.send(f"{ctx.author.mention} is now divorced. 💔")

    @commands.group(invoke_without_command=True)
    async def pet(self, ctx):
        """Pet system commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @pet.command()
    async def adopt(self, ctx, name: str, type: str):
        """Adopt a pet"""
        try:
            await self.bot.db.execute(
                '''INSERT INTO pets (owner_id, name, type)
                   VALUES ($1, $2, $3)''',
                ctx.author.id, name, type.lower()
            )
            await ctx.send(f"You've adopted a {type} named {name}! 🐾")
        except Exception as e:
            await ctx.send(f"Error adopting pet: {e}")

    @pet.command()
    async def train(self, ctx, name: str):
        """Train your pet"""
        # Check cooldown
        if ctx.author.id in self.pet_cooldowns:
            remaining = self.pet_cooldowns[ctx.author.id] - ctx.message.created_at.timestamp()
            if remaining > 0:
                return await ctx.send(f"You can train again in {int(remaining)} seconds.")

        try:
            pet = await self.bot.db.fetchrow(
                'SELECT * FROM pets WHERE owner_id = $1 AND name = $2',
                ctx.author.id, name
            )
            if not pet:
                return await ctx.send("You don't have a pet with that name!")

            # Update pet stats
            stats = pet['stats'] or {}
            stats['level'] = stats.get('level', 0) + 1
            stats['experience'] = stats.get('experience', 0) + random.randint(10, 20)

            await self.bot.db.execute(
                'UPDATE pets SET stats = $1 WHERE id = $2',
                stats, pet['id']
            )

            # Set cooldown (1 hour)
            self.pet_cooldowns[ctx.author.id] = ctx.message.created_at.timestamp() + 3600

            await ctx.send(
                f"{name} completed their training! 🎓\n"
                f"Level: {stats['level']}\n"
                f"Experience: {stats['experience']}"
            )
        except Exception as e:
            await ctx.send(f"Error training pet: {e}")

    @commands.command()
    async def hangman(self, ctx):
        """Play hangman"""
        words = ["discord", "python", "gaming", "computer", "internet", "programming"]
        word = random.choice(words)
        guessed = set()
        tries = 6

        def get_display():
            return " ".join(letter if letter in guessed else "_" for letter in word)

        message = await ctx.send(
            f"Hangman Game!\nWord: {get_display()}\n"
            f"Tries left: {tries}\nGuessed letters: {', '.join(sorted(guessed))}"
        )

        while tries > 0:
            if all(letter in guessed for letter in word):
                await ctx.send(f"You won! The word was {word}! 🎉")
                return

            try:
                guess = await self.bot.wait_for(
                    'message',
                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel and \
                                  len(m.content) == 1 and m.content.isalpha(),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                await ctx.send("Game over - you took too long!")
                return

            letter = guess.content.lower()
            if letter in guessed:
                await ctx.send("You already guessed that letter!")
                continue

            guessed.add(letter)
            if letter not in word:
                tries -= 1
                if tries == 0:
                    await ctx.send(f"Game over! The word was {word}!")
                    return

            await message.edit(content=
                f"Hangman Game!\nWord: {get_display()}\n"
                f"Tries left: {tries}\nGuessed letters: {', '.join(sorted(guessed))}"
            )

    @commands.command()
    async def trivia(self, ctx):
        """Play a trivia game"""
        questions = [
            {
                "question": "What programming language is Discord.py written in?",
                "answer": "python"
            },
            {
                "question": "What year was Discord launched?",
                "answer": "2015"
            },
            {
                "question": "What is the maximum length of a Discord message?",
                "answer": "2000"
            }
        ]

        question = random.choice(questions)
        await ctx.send(f"**Trivia Time!**\n{question['question']}")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            guess = await self.bot.wait_for('message', check=check, timeout=30.0)
            if guess.content.lower() == question['answer'].lower():
                await ctx.send("Correct! 🎉")
            else:
                await ctx.send(f"Wrong! The answer was {question['answer']}.")
        except asyncio.TimeoutError:
            await ctx.send(f"Time's up! The answer was {question['answer']}.")

async def setup(bot):
    await bot.add_cog(FunCommands(bot)) 