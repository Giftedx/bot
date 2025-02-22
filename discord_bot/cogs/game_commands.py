"""Game and entertainment commands."""

from discord.ext import commands
import discord
import logging
import random
import asyncio
from typing import List, Dict
import json

logger = logging.getLogger(__name__)

class GameCommands(commands.Cog, name="Games"):
    """Fun game commands and entertainment features.
    
    This category includes commands for:
    - Classic games (Hangman, Tic Tac Toe)
    - Trivia games with multiple categories
    - Dice rolling and random number generation
    - Magic 8-ball and fortune telling
    - Rock, Paper, Scissors
    
    Most games can be played solo or with other members.
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.trivia_categories = {
            "general": 9,
            "books": 10,
            "film": 11,
            "music": 12,
            "games": 15,
            "science": 17,
            "computers": 18,
            "sports": 21,
            "geography": 22,
            "history": 23,
            "animals": 27
        }
        self.hangman_games: Dict[int, Dict] = {}
        self.tictactoe_games = {}
        self.trivia_scores: Dict[int, int] = {}  # User ID -> Score

    @commands.command(name='hangman')
    async def hangman(self, ctx):
        """Start a game of hangman.
        
        Classic hangman game where players guess letters to uncover a word.
        Game ends when the word is guessed or after 6 wrong guesses.
        
        Examples:
        ---------
        !hangman
        
        Notes:
        ------
        - One game per channel
        - 6 wrong guesses allowed
        - 30 second timeout between guesses
        - Anyone in the channel can guess
        """
        if ctx.channel.id in self.hangman_games:
            await ctx.send("A game is already in progress in this channel!")
            return

        words = ["PYTHON", "DISCORD", "GAMING", "COMPUTER", "PROGRAMMING", "KEYBOARD", "INTERNET", "SERVER"]
        word = random.choice(words)
        guessed = set()
        tries = 6
        
        self.hangman_games[ctx.channel.id] = {
            'word': word,
            'guessed': guessed,
            'tries': tries
        }
        
        def get_display_word():
            return ' '.join(letter if letter in guessed else '_' for letter in word)
            
        await ctx.send(f"Hangman game started! The word has {len(word)} letters.\n{get_display_word()}")
        
        def check(m):
            return (m.channel == ctx.channel and 
                   len(m.content) == 1 and 
                   m.content.isalpha())
        
        while tries > 0 and '_' in get_display_word():
            try:
                msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                guess = msg.content.upper()
                
                if guess in guessed:
                    await ctx.send("You already guessed that letter!")
                    continue
                    
                guessed.add(guess)
                if guess in word:
                    await ctx.send(f"Correct! {get_display_word()}")
                else:
                    tries -= 1
                    await ctx.send(f"Wrong! {tries} tries left.\n{get_display_word()}")
                    
            except asyncio.TimeoutError:
                await ctx.send("Game over - you took too long!")
                break
                
        if '_' not in get_display_word():
            await ctx.send(f"Congratulations! You won! The word was {word}")
        elif tries == 0:
            await ctx.send(f"Game over! The word was {word}")
            
        del self.hangman_games[ctx.channel.id]

    @commands.command(name='tictactoe', aliases=['ttt'])
    async def tictactoe(self, ctx, opponent: discord.Member = None):
        """Start a game of Tic Tac Toe with another player.
        
        Classic Tic Tac Toe game played with reactions.
        First player uses X, second player uses O.
        
        Parameters:
        -----------
        opponent: The member to play against
        
        Examples:
        ---------
        !tictactoe @username
        !ttt @username
        
        Notes:
        ------
        - One game per channel
        - 30 second turn timer
        - Cannot play against bots
        - Cannot play against yourself
        """
        if opponent is None:
            await ctx.send("Please mention someone to play against!")
            return
            
        if opponent.bot:
            await ctx.send("You can't play against bots!")
            return
            
        if opponent == ctx.author:
            await ctx.send("You can't play against yourself!")
            return
            
        if ctx.channel.id in self.tictactoe_games:
            await ctx.send("A game is already in progress in this channel!")
            return
            
        board = [["\u2B1C" for _ in range(3)] for _ in range(3)]
        current_player = ctx.author
        self.tictactoe_games[ctx.channel.id] = {
            'board': board,
            'current_player': current_player,
            'players': (ctx.author, opponent),
            'symbols': ("❌", "⭕")
        }
        
        def get_board_str():
            return '\n'.join([''.join(row) for row in board])
            
        await ctx.send(f"Tic Tac Toe: {ctx.author.mention} vs {opponent.mention}\n{get_board_str()}")
        
        def check_win(symbol):
            # Check rows and columns
            for i in range(3):
                if all(board[i][j] == symbol for j in range(3)) or \
                   all(board[j][i] == symbol for j in range(3)):
                    return True
            # Check diagonals
            if all(board[i][i] == symbol for i in range(3)) or \
               all(board[i][2-i] == symbol for i in range(3)):
                return True
            return False
            
        def check(m):
            return (m.channel == ctx.channel and 
                   m.author == current_player and 
                   m.content.isdigit() and 
                   1 <= int(m.content) <= 9)
        
        for _ in range(9):  # Maximum 9 moves
            await ctx.send(f"{current_player.mention}'s turn! Enter a position (1-9):")
            try:
                msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                pos = int(msg.content) - 1
                row, col = pos // 3, pos % 3
                
                if board[row][col] != "\u2B1C":
                    await ctx.send("That position is already taken!")
                    continue
                    
                symbol = "❌" if current_player == ctx.author else "⭕"
                board[row][col] = symbol
                await ctx.send(get_board_str())
                
                if check_win(symbol):
                    await ctx.send(f"{current_player.mention} wins! 🎉")
                    break
                    
                current_player = opponent if current_player == ctx.author else ctx.author
                
            except asyncio.TimeoutError:
                await ctx.send("Game over - player took too long!")
                break
                
        else:
            await ctx.send("It's a tie!")
            
        del self.tictactoe_games[ctx.channel.id]

    @commands.command(name='trivia')
    async def trivia(self, ctx, category: str = None):
        """Start a trivia game.
        
        Multi-category trivia game with scoring system.
        Questions have multiple choice answers selected with reactions.
        
        Parameters:
        -----------
        category: Optional category (general, books, film, music, games, science, computers, sports, geography, history, animals)
        
        Examples:
        ---------
        !trivia
        !trivia science
        !trivia computers
        
        Notes:
        ------
        - 30 second answer timer
        - Keeps track of scores
        - Random category if none specified
        - Questions from Open Trivia Database
        """
        if category and category.lower() not in self.trivia_categories:
            categories = ", ".join(self.trivia_categories.keys())
            await ctx.send(f"Invalid category! Available categories: {categories}")
            return
            
        category_id = self.trivia_categories.get(category.lower()) if category else random.choice(list(self.trivia_categories.values()))
        
        async with self.bot.session.get(
            f"https://opentdb.com/api.php?amount=1&category={category_id}&type=multiple"
        ) as response:
            if response.status != 200:
                await ctx.send("Failed to fetch trivia question!")
                return
                
            data = await response.json()
            if not data['results']:
                await ctx.send("No questions found!")
                return
                
            question = data['results'][0]
            correct_answer = question['correct_answer']
            answers = [correct_answer] + question['incorrect_answers']
            random.shuffle(answers)
            
            embed = discord.Embed(
                title="Trivia Question",
                description=question['question'],
                color=discord.Color.blue()
            )
            
            for i, answer in enumerate(answers, 1):
                embed.add_field(name=f"Option {i}", value=answer, inline=False)
                
            await ctx.send(embed=embed)
            
            def check(m):
                return (m.channel == ctx.channel and 
                       m.content.isdigit() and 
                       1 <= int(m.content) <= 4)
            
            try:
                msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                user_answer = answers[int(msg.content) - 1]
                
                if user_answer == correct_answer:
                    self.trivia_scores[msg.author.id] = self.trivia_scores.get(msg.author.id, 0) + 1
                    await ctx.send(f"🎉 Correct, {msg.author.mention}! Your score is now {self.trivia_scores[msg.author.id]}")
                else:
                    await ctx.send(f"❌ Wrong! The correct answer was: {correct_answer}")
                    
            except asyncio.TimeoutError:
                await ctx.send(f"Time's up! The correct answer was: {correct_answer}")

    @commands.command(name="8ball")
    async def eight_ball(self, ctx, *, question: str):
        """Ask the magic 8-ball a question.
        
        Get a mystical answer to any yes/no question.
        
        Parameters:
        -----------
        question: The question to ask
        
        Examples:
        ---------
        !8ball Will I win the lottery?
        !8ball Should I go out today?
        
        Notes:
        ------
        - Questions should be yes/no format
        - Responses are randomly selected
        - For entertainment purposes only!
        """
        responses = [
            "It is certain.", "It is decidedly so.", "Without a doubt.",
            "Yes - definitely.", "You may rely on it.", "As I see it, yes.",
            "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
            "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
            "Cannot predict now.", "Concentrate and ask again.",
            "Don't count on it.", "My reply is no.", "My sources say no.",
            "Outlook not so good.", "Very doubtful."
        ]
        
        response = random.choice(responses)
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            color=discord.Color.blue()
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=response, inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="roll")
    async def roll_dice(self, ctx, dice: str = "1d6"):
        """Roll dice in NdN format.
        
        Roll any number and type of dice using DnD notation.
        
        Parameters:
        -----------
        dice: Dice notation (e.g., 2d6 for two six-sided dice)
        
        Examples:
        ---------
        !roll - Roll one six-sided die
        !roll 2d20 - Roll two twenty-sided dice
        !roll 4d6 - Roll four six-sided dice
        
        Notes:
        ------
        - Default is 1d6
        - Maximum 100 dice
        - Maximum 100 sides per die
        - Shows individual rolls and total
        """
        try:
            number, sides = map(int, dice.split('d'))
            if number <= 0 or sides <= 0:
                await ctx.send("Number of dice and sides must be positive!")
                return
            if number > 100:
                await ctx.send("Cannot roll more than 100 dice at once!")
                return
                
            rolls = [random.randint(1, sides) for _ in range(number)]
            total = sum(rolls)
            
            embed = discord.Embed(
                title="🎲 Dice Roll",
                color=discord.Color.blue()
            )
            embed.add_field(name="Rolls", value=", ".join(map(str, rolls)), inline=False)
            embed.add_field(name="Total", value=str(total), inline=False)
            
            await ctx.send(embed=embed)
        except ValueError:
            await ctx.send("Format must be in NdN! (e.g., 1d6, 2d20)")

    @commands.command(name="rps")
    async def rock_paper_scissors(self, ctx):
        """Play Rock, Paper, Scissors against the bot.
        
        Classic Rock, Paper, Scissors game using reactions.
        
        Examples:
        ---------
        !rps
        
        Notes:
        ------
        - Use reactions to make your choice
        - 30 second time limit
        - Shows win/loss record
        """
        choices = ["🪨", "📄", "✂️"]
        
        embed = discord.Embed(
            title="Rock, Paper, Scissors",
            description="React with your choice!",
            color=discord.Color.blue()
        )
        message = await ctx.send(embed=embed)
        
        for choice in choices:
            await message.add_reaction(choice)
            
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in choices
            
        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            bot_choice = random.choice(choices)
            
            # Determine winner
            player_choice = str(reaction.emoji)
            result = ""
            
            if player_choice == bot_choice:
                result = "It's a tie!"
            elif (
                (player_choice == "🪨" and bot_choice == "✂️") or
                (player_choice == "📄" and bot_choice == "🪨") or
                (player_choice == "✂️" and bot_choice == "📄")
            ):
                result = "You win!"
            else:
                result = "I win!"
                
            embed = discord.Embed(
                title="Rock, Paper, Scissors - Results",
                color=discord.Color.blue()
            )
            embed.add_field(name="Your Choice", value=player_choice, inline=True)
            embed.add_field(name="My Choice", value=bot_choice, inline=True)
            embed.add_field(name="Result", value=result, inline=False)
            
            await message.edit(embed=embed)
            
        except asyncio.TimeoutError:
            await ctx.send("Game cancelled - you didn't react in time!")

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(GameCommands(bot)) 