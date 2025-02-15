import discord
from discord.ext import commands
import random
import asyncio
from typing import Dict

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games: Dict[int, Dict] = {}

    @commands.group(invoke_without_command=True)
    async def game(self, ctx):
        """Game commands group"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Available Games",
                description="Use `!game <name>` to start a game:\n"
                          "• trivia - Start a trivia game\n"
                          "• hangman - Play hangman\n"
                          "• tictactoe - Play Tic Tac Toe\n"
                          "• rps - Play Rock, Paper, Scissors",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)

    @game.command()
    async def trivia(self, ctx):
        """Start a trivia game"""
        # Sample trivia questions (you can expand this)
        questions = [
            {
                "question": "What is the capital of France?",
                "answer": "paris",
                "options": ["London", "Paris", "Berlin", "Madrid"]
            },
            {
                "question": "Which planet is known as the Red Planet?",
                "answer": "mars",
                "options": ["Venus", "Mars", "Jupiter", "Saturn"]
            }
        ]
        
        question = random.choice(questions)
        options_text = "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(question["options"]))
        
        embed = discord.Embed(
            title="Trivia Time!",
            description=f"{question['question']}\n\n{options_text}",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for('message', timeout=30.0, check=check)
            if msg.content.lower() == question["answer"]:
                await ctx.send("Correct! 🎉")
            else:
                await ctx.send(f"Wrong! The answer was {question['answer'].title()}")
        except asyncio.TimeoutError:
            await ctx.send("Time's up! ⏰")

    @game.command()
    async def tictactoe(self, ctx, opponent: discord.Member = None):
        """Play Tic Tac Toe"""
        if not opponent:
            return await ctx.send("Please mention an opponent to play with!")
        
        if opponent.bot:
            return await ctx.send("You can't play against bots!")
        
        if opponent == ctx.author:
            return await ctx.send("You can't play against yourself!")

        # Initialize game
        game = {
            'board': [':white_large_square:'] * 9,
            'current_player': ctx.author,
            'players': {
                ctx.author: '❌',
                opponent: '⭕'
            }
        }
        self.active_games[ctx.channel.id] = game

        # Display board
        board_msg = await self.display_board(ctx, game['board'])
        await ctx.send(f"{ctx.author.mention} vs {opponent.mention}\n{ctx.author.mention}'s turn!")

        def check(m):
            return (
                m.author in game['players'] and
                m.channel == ctx.channel and
                m.content.isdigit() and
                1 <= int(m.content) <= 9
            )

        # Game loop
        while True:
            try:
                msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                position = int(msg.content) - 1

                # Check if valid move
                if game['board'][position] != ':white_large_square:':
                    await ctx.send("That position is already taken!")
                    continue

                # Make move
                game['board'][position] = game['players'][game['current_player']]
                await self.display_board(ctx, game['board'])

                # Check for win
                if self.check_win(game['board']):
                    await ctx.send(f"{game['current_player'].mention} wins! 🎉")
                    break

                # Check for tie
                if ':white_large_square:' not in game['board']:
                    await ctx.send("It's a tie! 🤝")
                    break

                # Switch players
                game['current_player'] = opponent if game['current_player'] == ctx.author else ctx.author
                await ctx.send(f"{game['current_player'].mention}'s turn!")

            except asyncio.TimeoutError:
                await ctx.send("Game timed out! ⏰")
                break

        del self.active_games[ctx.channel.id]

    async def display_board(self, ctx, board):
        """Display the Tic Tac Toe board"""
        rows = [board[i:i+3] for i in range(0, 9, 3)]
        board_str = "\n".join(" ".join(row) for row in rows)
        await ctx.send(board_str)

    def check_win(self, board):
        """Check for a win in Tic Tac Toe"""
        # Check rows
        for i in range(0, 9, 3):
            if board[i] == board[i+1] == board[i+2] != ':white_large_square:':
                return True
        # Check columns
        for i in range(3):
            if board[i] == board[i+3] == board[i+6] != ':white_large_square:':
                return True
        # Check diagonals
        if board[0] == board[4] == board[8] != ':white_large_square:':
            return True
        if board[2] == board[4] == board[6] != ':white_large_square:':
            return True
        return False

    @game.command()
    async def rps(self, ctx, opponent: discord.Member = None):
        """Play Rock, Paper, Scissors"""
        if not opponent:
            return await ctx.send("Please mention an opponent to play with!")
        
        if opponent.bot:
            return await ctx.send("You can't play against bots!")
        
        if opponent == ctx.author:
            return await ctx.send("You can't play against yourself!")

        await ctx.send(f"{ctx.author.mention} has challenged {opponent.mention} to Rock, Paper, Scissors!")
        await ctx.send("Please DM me your choice (rock/paper/scissors)")

        choices = {}

        def check(m):
            return (
                m.author in [ctx.author, opponent] and
                isinstance(m.channel, discord.DMChannel) and
                m.content.lower() in ['rock', 'paper', 'scissors']
            )

        try:
            for player in [ctx.author, opponent]:
                await player.send("Enter your choice (rock/paper/scissors):")
                choice = await self.bot.wait_for('message', timeout=30.0, check=lambda m: check(m) and m.author == player)
                choices[player] = choice.content.lower()

            # Determine winner
            result = self.determine_rps_winner(choices[ctx.author], choices[opponent])
            
            if result == 0:
                await ctx.send("It's a tie! 🤝")
            elif result == 1:
                await ctx.send(f"{ctx.author.mention} wins! 🎉")
            else:
                await ctx.send(f"{opponent.mention} wins! 🎉")

            await ctx.send(f"{ctx.author.mention} chose {choices[ctx.author]}\n{opponent.mention} chose {choices[opponent]}")

        except asyncio.TimeoutError:
            await ctx.send("Game timed out! ⏰")

    def determine_rps_winner(self, choice1, choice2):
        """Determine the winner of Rock, Paper, Scissors"""
        if choice1 == choice2:
            return 0  # Tie
        
        winning_moves = {
            'rock': 'scissors',
            'paper': 'rock',
            'scissors': 'paper'
        }
        
        return 1 if winning_moves[choice1] == choice2 else 2

async def setup(bot):
    await bot.add_cog(Games(bot)) 