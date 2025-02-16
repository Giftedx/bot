"""Discord bot commands for controlling Plex media playback."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from .discord_activity import DiscordPlexActivity
from .plex_client import PlexClient

class PlexCommands(commands.Cog):
    """Commands for controlling Plex media playback in voice channels."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the Plex commands.
        
        Args:
            bot: The Discord bot instance.
        """
        self.bot = bot
        self.plex = PlexClient()
        self.activity = DiscordPlexActivity(bot)
        
    @app_commands.command(name="plex-search")
    async def search(self, 
                    interaction: discord.Interaction, 
                    query: str,
                    media_type: Optional[str] = None):
        """Search for media on your Plex server.
        
        Args:
            interaction: The Discord interaction.
            query: Search query string.
            media_type: Optional media type filter.
        """
        await interaction.response.defer()
        
        try:
            results = self.plex.search_media(query, media_type)
            
            if not results:
                await interaction.followup.send("No results found.")
                return
                
            # Create embed with results
            embed = discord.Embed(
                title="Plex Search Results",
                color=discord.Color.blue()
            )
            
            for i, media in enumerate(results[:10], 1):
                title = media['title']
                if media['type'] == 'movie':
                    details = f"({media['year']}) - {media['duration']//60000} minutes"
                elif media['type'] == 'show':
                    details = f"({media['year']}) - {media['seasons']} seasons"
                else:
                    details = f"{media['artist']} - {media['album']}"
                    
                embed.add_field(
                    name=f"{i}. {title}",
                    value=details,
                    inline=False
                )
                
            # Add select menu for choosing media
            select = discord.ui.Select(
                placeholder="Choose media to play",
                options=[
                    discord.SelectOption(
                        label=f"{i}. {media['title'][:80]}",
                        value=media['key']
                    ) for i, media in enumerate(results[:10], 1)
                ]
            )
            
            async def select_callback(interaction: discord.Interaction):
                media_key = select.values[0]
                
                # Check if user is in voice channel
                if not interaction.user.voice:
                    await interaction.response.send_message(
                        "You must be in a voice channel to play media.",
                        ephemeral=True
                    )
                    return
                    
                # Start playback
                try:
                    await self.activity.create_activity(
                        interaction.user.voice.channel.id,
                        media_key
                    )
                    await interaction.response.send_message(
                        "Starting playback...",
                        ephemeral=True
                    )
                except Exception as e:
                    await interaction.response.send_message(
                        f"Failed to start playback: {str(e)}",
                        ephemeral=True
                    )
                    
            select.callback = select_callback
            
            view = discord.ui.View()
            view.add_item(select)
            
            await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}")
            
    @app_commands.command(name="plex-recent")
    async def recent(self,
                    interaction: discord.Interaction,
                    limit: Optional[int] = 10,
                    media_type: Optional[str] = None):
        """Show recently added media on your Plex server.
        
        Args:
            interaction: The Discord interaction.
            limit: Maximum number of items to show.
            media_type: Optional media type filter.
        """
        await interaction.response.defer()
        
        try:
            results = self.plex.get_recently_added(limit, media_type)
            
            if not results:
                await interaction.followup.send("No recent media found.")
                return
                
            # Create embed with results
            embed = discord.Embed(
                title="Recently Added to Plex",
                color=discord.Color.blue()
            )
            
            for i, media in enumerate(results, 1):
                title = media['title']
                if media['type'] == 'movie':
                    details = f"({media['year']}) - {media['duration']//60000} minutes"
                elif media['type'] == 'show':
                    details = f"Season {media['season']} Episode {media['episode']}"
                else:
                    details = f"{media['artist']} - {media['album']}"
                    
                embed.add_field(
                    name=f"{i}. {title}",
                    value=details,
                    inline=False
                )
                
            # Add select menu for choosing media
            select = discord.ui.Select(
                placeholder="Choose media to play",
                options=[
                    discord.SelectOption(
                        label=f"{i}. {media['title'][:80]}",
                        value=media['key']
                    ) for i, media in enumerate(results, 1)
                ]
            )
            
            async def select_callback(interaction: discord.Interaction):
                media_key = select.values[0]
                
                # Check if user is in voice channel
                if not interaction.user.voice:
                    await interaction.response.send_message(
                        "You must be in a voice channel to play media.",
                        ephemeral=True
                    )
                    return
                    
                # Start playback
                try:
                    await self.activity.create_activity(
                        interaction.user.voice.channel.id,
                        media_key
                    )
                    await interaction.response.send_message(
                        "Starting playback...",
                        ephemeral=True
                    )
                except Exception as e:
                    await interaction.response.send_message(
                        f"Failed to start playback: {str(e)}",
                        ephemeral=True
                    )
                    
            select.callback = select_callback
            
            view = discord.ui.View()
            view.add_item(select)
            
            await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}")
            
    @app_commands.command(name="plex-stop")
    async def stop(self, interaction: discord.Interaction):
        """Stop the current media playback.
        
        Args:
            interaction: The Discord interaction.
        """
        if not self.activity.is_playing():
            await interaction.response.send_message(
                "Nothing is currently playing.",
                ephemeral=True
            )
            return
            
        await self.activity.end_activity()
        await interaction.response.send_message(
            "Playback stopped.",
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    """Add the cog to the bot."""
    await bot.add_cog(PlexCommands(bot)) 