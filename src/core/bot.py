import discord
from discord.ext import commands, tasks
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
import random
import asyncio
import json

from .database import DatabaseManager
from .personal_system import PersonalSystem

logger = logging.getLogger(__name__)

class PersonalBot(commands.Bot):
    """Discord bot for personal content and cross-game features"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=commands.DefaultHelpCommand(
                no_category='General Commands'
            )
        )
        
        # Initialize systems
        self.db = DatabaseManager()
        self.personal_system = PersonalSystem()
        
        # Runtime state
        self.active_sessions = {}
        self.watch_parties = {}
        self.roast_cooldowns = {}
        
        # Load commands
        self.load_commands()
        
        # Start background tasks
        self.cleanup_expired_effects.start()
        self.check_events.start()
        self.process_roasts.start()
    
    def load_commands(self) -> None:
        """Load bot commands"""
        
        @self.command(name='pet')
        async def pet_command(ctx, action: str, pet_name: Optional[str] = None):
            """Pet system commands"""
            player_id = str(ctx.author.id)
            
            if action == 'list':
                pets = self.db.get_player_pets(player_id)
                if not pets:
                    await ctx.send("You don't have any pets yet!")
                    return
                
                pet_list = "\n".join(
                    f"• {pet['name']} ({pet['type']})"
                    for pet in pets
                )
                await ctx.send(f"Your pets:\n{pet_list}")
                
            elif action == 'info' and pet_name:
                pets = self.db.get_player_pets(player_id)
                pet = next((p for p in pets if p['name'].lower() == pet_name.lower()), None)
                
                if not pet:
                    await ctx.send(f"You don't have a pet named {pet_name}!")
                    return
                
                pet_data = pet['data']
                info = (
                    f"**{pet['name']}** ({pet['type']})\n"
                    f"Stats:\n"
                    f"• Happiness: {pet_data['stats']['happiness']}/100\n"
                    f"• Loyalty: {pet_data['stats']['loyalty']}/100\n"
                    f"• Experience: {pet_data['stats']['experience']}\n\n"
                    f"Abilities:"
                )
                
                for ability, data in pet_data['abilities'].items():
                    status = "✅" if data['unlocked'] else "❌"
                    info += f"\n• {ability}: {status}"
                
                await ctx.send(info)
                
            elif action == 'interact' and pet_name:
                result = self.personal_system.pet_manager.interact_with_pet(
                    player_id, pet_name, 'basic_interaction'
                )
                
                if not result['success']:
                    await ctx.send(result['message'])
                    return
                
                response = f"You interact with {pet_name}!"
                if 'effects' in result:
                    for effect in result['effects']:
                        response += f"\n• {effect['type']}"
                
                if 'special_event' in result:
                    response += f"\n\n**Special Event!**\n{result['special_event']['message']}"
                
                await ctx.send(response)
        
        @self.command(name='watch')
        async def watch_command(ctx, action: str, *, args: Optional[str] = None):
            """Plex watch party commands"""
            player_id = str(ctx.author.id)
            
            if action == 'start':
                if not args:
                    await ctx.send("Please specify what you want to watch!")
                    return
                
                # Create watch party
                party_id = str(random.randint(1000, 9999))
                self.watch_parties[party_id] = {
                    'host': player_id,
                    'content': args,
                    'members': [player_id],
                    'started_at': datetime.now().isoformat(),
                    'status': 'waiting'
                }
                
                await ctx.send(
                    f"Watch party created! ID: {party_id}\n"
                    f"Content: {args}\n"
                    f"Use `!watch join {party_id}` to join!"
                )
                
            elif action == 'join':
                if not args:
                    await ctx.send("Please specify the watch party ID!")
                    return
                
                party = self.watch_parties.get(args)
                if not party:
                    await ctx.send("Watch party not found!")
                    return
                
                if player_id in party['members']:
                    await ctx.send("You're already in this watch party!")
                    return
                
                party['members'].append(player_id)
                await ctx.send(f"Joined watch party {args}!")
                
            elif action == 'start_watching' and args:
                party = self.watch_parties.get(args)
                if not party:
                    await ctx.send("Watch party not found!")
                    return
                
                if player_id != party['host']:
                    await ctx.send("Only the host can start watching!")
                    return
                
                party['status'] = 'watching'
                started_at = datetime.now()
                
                # Record watch for all members
                for member_id in party['members']:
                    self.db.add_watch_record(member_id, {
                        'id': args,
                        'type': 'group_watch',
                        'title': party['content'],
                        'started_at': started_at.isoformat()
                    })
                
                await ctx.send("Watch party started! Enjoy!")
        
        @self.command(name='roast')
        async def roast_command(ctx, target: Optional[discord.Member] = None):
            """Generate a roast"""
            player_id = str(ctx.author.id)
            
            # Check cooldown
            if player_id in self.roast_cooldowns:
                remaining = self.roast_cooldowns[player_id] - datetime.now()
                if remaining.total_seconds() > 0:
                    await ctx.send(f"Please wait {int(remaining.total_seconds())} seconds before roasting again!")
                    return
            
            # Get roastable messages
            messages = self.db.get_roastable_messages(min_score=0.7, limit=10)
            if not messages:
                await ctx.send("No roastable messages found!")
                return
            
            # Filter by target if specified
            if target:
                messages = [
                    m for m in messages 
                    if m['player_id'] == str(target.id)
                ]
                if not messages:
                    await ctx.send(f"No roastable messages found for {target.display_name}!")
                    return
            
            # Select message and generate roast
            message = random.choice(messages)
            roast = self.personal_system.joke_manager.generate_roast(message)
            
            # Record roast
            self.db.add_roast(message['message_id'], roast['message'])
            
            # Set cooldown
            self.roast_cooldowns[player_id] = datetime.now() + timedelta(minutes=5)
            
            # Send roast
            user = self.get_user(int(message['player_id']))
            username = user.display_name if user else "someone"
            
            await ctx.send(f"Remember when {username} said '{message['message']}'?\n{roast['message']}")
        
        @self.command(name='effects')
        async def effects_command(ctx):
            """Show active effects"""
            player_id = str(ctx.author.id)
            effects = self.db.get_active_effects(player_id)
            
            if not effects:
                await ctx.send("You have no active effects!")
                return
            
            effect_list = "**Active Effects:**\n"
            for effect in effects:
                duration = ""
                if effect['expires_at']:
                    expires = datetime.fromisoformat(effect['expires_at'])
                    remaining = expires - datetime.now()
                    if remaining.total_seconds() > 0:
                        duration = f" ({int(remaining.total_seconds())}s remaining)"
                
                effect_list += f"\n• {effect['type']} from {effect['source']}{duration}"
            
            await ctx.send(effect_list)
    
    async def on_ready(self):
        """Bot ready event"""
        logger.info(f"Logged in as {self.user.name} ({self.user.id})")
        
        # Initialize database
        try:
            self.db.setup_database()
            logger.info("Database initialized")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    async def on_message(self, message):
        """Message event handler"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Process commands
        await self.process_commands(message)
        
        # Log message for potential roasts
        try:
            score = self.personal_system.joke_manager.score_message(message.content)
            self.db.log_chat_message(
                str(message.author.id),
                str(message.channel.id),
                message.content,
                score
            )
        except Exception as e:
            logger.error(f"Error logging message: {e}")
        
        # Check for easter eggs
        try:
            easter_egg = self.personal_system.joke_manager.check_triggers({
                'message': message.content,
                'player': str(message.author.id),
                'channel': str(message.channel.id)
            })
            
            if easter_egg:
                await message.channel.send(easter_egg['message'])
        except Exception as e:
            logger.error(f"Error checking easter eggs: {e}")
    
    @tasks.loop(minutes=5)
    async def cleanup_expired_effects(self):
        """Clean up expired effects periodically"""
        try:
            self.db.cleanup_expired_effects()
        except Exception as e:
            logger.error(f"Error cleaning up effects: {e}")
    
    @tasks.loop(minutes=1)
    async def check_events(self):
        """Check for events periodically"""
        try:
            events = self.personal_system.event_manager.update_events()
            
            for event in events:
                # Find appropriate channel
                channel = self.get_channel(self.config['event_channel_id'])
                if not channel:
                    continue
                
                # Announce event
                await channel.send(
                    f"**New Event!**\n"
                    f"Type: {event['type']}\n"
                    f"Duration: {event.get('duration', 'Unlimited')}\n"
                    f"{event.get('description', '')}"
                )
        except Exception as e:
            logger.error(f"Error checking events: {e}")
    
    @tasks.loop(minutes=15)
    async def process_roasts(self):
        """Process roasts periodically"""
        try:
            # Get channels where roasts are enabled
            roast_channels = [
                self.get_channel(channel_id)
                for channel_id in self.config['roast_channel_ids']
            ]
            
            if not roast_channels:
                return
            
            # Check for roastable messages
            messages = self.db.get_roastable_messages(min_score=0.8, limit=5)
            if not messages:
                return
            
            # Generate and send roasts
            for message in messages:
                if random.random() < 0.3:  # 30% chance to roast
                    roast = self.personal_system.joke_manager.generate_roast(message)
                    self.db.add_roast(message['message_id'], roast['message'])
                    
                    # Send to random enabled channel
                    channel = random.choice(roast_channels)
                    user = self.get_user(int(message['player_id']))
                    username = user.display_name if user else "someone"
                    
                    await channel.send(
                        f"Remember when {username} said '{message['message']}'?\n"
                        f"{roast['message']}"
                    )
                    
                    # Wait between roasts
                    await asyncio.sleep(random.randint(30, 300))
        except Exception as e:
            logger.error(f"Error processing roasts: {e}")
    
    def run(self, token: str, **kwargs):
        """Run the bot"""
        try:
            super().run(token, **kwargs)
        except Exception as e:
            logger.error(f"Bot runtime error: {e}")
        finally:
            # Clean up
            self.db.close() 