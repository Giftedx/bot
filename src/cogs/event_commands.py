from discord.ext import commands
import discord
from typing import Optional
import logging
from datetime import datetime, timedelta
import random
import asyncio

logger = logging.getLogger(__name__)

class EventCommands(commands.Cog):
    """Cross-game event commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_events = {}
        self.event_tasks = {}
    
    def cog_unload(self):
        """Clean up when cog is unloaded"""
        for task in self.event_tasks.values():
            task.cancel()
    
    @commands.group(name='event', invoke_without_command=True)
    async def event(self, ctx):
        """Event system commands"""
        await ctx.send_help(ctx.command)
    
    @event.command(name='list')
    async def event_list(self, ctx):
        """List active events"""
        events = self.bot.db.get_active_events()
        
        if not events:
            await ctx.send("No active events!")
            return
        
        # Create embed
        embed = discord.Embed(
            title="Active Events",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # Group events by type
        events_by_type = {}
        for event in events:
            event_type = event['type']
            if event_type not in events_by_type:
                events_by_type[event_type] = []
            events_by_type[event_type].append(event)
        
        # Add fields for each type
        for event_type, type_events in events_by_type.items():
            event_list = []
            for event in type_events:
                # Format duration
                duration = ""
                if event['ended_at']:
                    ends = datetime.fromisoformat(event['ended_at'])
                    remaining = ends - datetime.now()
                    if remaining.total_seconds() > 0:
                        hours = int(remaining.total_seconds() // 3600)
                        minutes = int((remaining.total_seconds() % 3600) // 60)
                        duration = f" ({hours}h {minutes}m remaining)"
                
                # Format event data
                data = event['data']
                effects = []
                for effect, value in data.get('effects', {}).items():
                    if isinstance(value, (int, float)):
                        symbol = "+" if value > 0 else ""
                        effects.append(f"{effect}: {symbol}{value}")
                    else:
                        effects.append(f"{effect}: {value}")
                
                event_list.append(
                    f"• {data.get('name', 'Unnamed Event')}{duration}\n"
                    f"  {', '.join(effects) if effects else data.get('description', 'No description')}"
                )
            
            embed.add_field(
                name=event_type.title(),
                value="\n".join(event_list),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @event.command(name='info')
    async def event_info(self, ctx, event_id: int):
        """Show detailed event information"""
        event = self.bot.db.get_event(event_id)
        if not event:
            await ctx.send("Event not found!")
            return
        
        # Create embed
        data = event['data']
        embed = discord.Embed(
            title=data.get('name', 'Unnamed Event'),
            description=data.get('description', 'No description available.'),
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # Add basic info
        embed.add_field(
            name="Type",
            value=event['type'],
            inline=True
        )
        
        embed.add_field(
            name="Status",
            value=event['status'].title(),
            inline=True
        )
        
        # Add duration
        started = datetime.fromisoformat(event['started_at'])
        embed.add_field(
            name="Started",
            value=started.strftime('%Y-%m-%d %H:%M:%S'),
            inline=True
        )
        
        if event['ended_at']:
            ends = datetime.fromisoformat(event['ended_at'])
            remaining = ends - datetime.now()
            if remaining.total_seconds() > 0:
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                embed.add_field(
                    name="Time Remaining",
                    value=f"{hours}h {minutes}m",
                    inline=True
                )
            else:
                embed.add_field(
                    name="Status",
                    value="Ended",
                    inline=True
                )
        
        # Add effects
        if 'effects' in data:
            effects = []
            for effect, value in data['effects'].items():
                if isinstance(value, (int, float)):
                    symbol = "+" if value > 0 else ""
                    effects.append(f"{effect}: {symbol}{value}")
                else:
                    effects.append(f"{effect}: {value}")
            
            embed.add_field(
                name="Effects",
                value="\n".join(effects),
                inline=False
            )
        
        # Add requirements if any
        if 'requirements' in data:
            reqs = []
            for req, value in data['requirements'].items():
                reqs.append(f"{req}: {value}")
            
            embed.add_field(
                name="Requirements",
                value="\n".join(reqs),
                inline=False
            )
        
        # Add rewards if any
        if 'rewards' in data:
            rewards = []
            for reward, value in data['rewards'].items():
                rewards.append(f"{reward}: {value}")
            
            embed.add_field(
                name="Rewards",
                value="\n".join(rewards),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @event.command(name='start')
    @commands.has_permissions(manage_messages=True)
    async def event_start(self, ctx, event_type: str, duration: str, *, name: str):
        """Start a new event (Mod only)"""
        # Parse duration
        try:
            value = int(duration[:-1])
            unit = duration[-1].lower()
            if unit == 'h':
                duration_seconds = value * 3600
            elif unit == 'm':
                duration_seconds = value * 60
            elif unit == 's':
                duration_seconds = value
            else:
                raise ValueError
        except ValueError:
            await ctx.send(
                "Invalid duration format! Use a number followed by h/m/s "
                "(e.g. 2h for 2 hours)"
            )
            return
        
        # Start event
        event_id = self.bot.db.start_event(
            event_type,
            {
                'name': name,
                'description': f"Started by {ctx.author.display_name}",
                'effects': {
                    'xp_multiplier': 1.5,
                    'drop_rate': 1.25
                }
            }
        )
        
        # Create embed
        embed = discord.Embed(
            title="Event Started",
            description=name,
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="Type",
            value=event_type,
            inline=True
        )
        
        embed.add_field(
            name="Duration",
            value=duration,
            inline=True
        )
        
        embed.add_field(
            name="Event ID",
            value=event_id,
            inline=True
        )
        
        # Add default effects
        embed.add_field(
            name="Effects",
            value=(
                "• XP Multiplier: +50%\n"
                "• Drop Rate: +25%"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        # Start cleanup task
        self.event_tasks[event_id] = asyncio.create_task(
            self.cleanup_event(event_id, duration_seconds)
        )
    
    @event.command(name='end')
    @commands.has_permissions(manage_messages=True)
    async def event_end(self, ctx, event_id: int):
        """End an event (Mod only)"""
        event = self.bot.db.get_event(event_id)
        if not event:
            await ctx.send("Event not found!")
            return
        
        # Add confirmation
        data = event['data']
        confirm = await ctx.send(
            f"Are you sure you want to end the event '{data.get('name', 'Unnamed Event')}'? "
            "React with ✅ to confirm."
        )
        await confirm.add_reaction("✅")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == "✅"
        
        try:
            await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except TimeoutError:
            await ctx.send("Event end cancelled.")
            return
        
        # End event
        self.bot.db.end_event(event_id)
        
        # Cancel cleanup task if exists
        if event_id in self.event_tasks:
            self.event_tasks[event_id].cancel()
            del self.event_tasks[event_id]
        
        await ctx.send(f"Ended event: {data.get('name', 'Unnamed Event')}")
    
    async def cleanup_event(self, event_id: int, duration: int):
        """Clean up an event after duration"""
        try:
            await asyncio.sleep(duration)
            
            # End event if still active
            event = self.bot.db.get_event(event_id)
            if event and event['active']:
                self.bot.db.end_event(event_id)
                
                # Send end message
                channel = self.bot.get_channel(
                    self.bot.config.get_config('channels.event_channel_id')
                )
                if channel:
                    data = event['data']
                    embed = discord.Embed(
                        title="Event Ended",
                        description=data.get('name', 'Unnamed Event'),
                        color=discord.Color.red(),
                        timestamp=datetime.now()
                    )
                    
                    await channel.send(embed=embed)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in event cleanup: {e}")
        finally:
            # Clean up task
            if event_id in self.event_tasks:
                del self.event_tasks[event_id]
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Restore event tasks on bot restart"""
        try:
            events = self.bot.db.get_active_events()
            for event in events:
                if event['ended_at']:
                    ends = datetime.fromisoformat(event['ended_at'])
                    remaining = (ends - datetime.now()).total_seconds()
                    if remaining > 0:
                        self.event_tasks[event['event_id']] = asyncio.create_task(
                            self.cleanup_event(event['event_id'], int(remaining))
                        )
        except Exception as e:
            logger.error(f"Error restoring event tasks: {e}")

async def setup(bot):
    await bot.add_cog(EventCommands(bot)) 