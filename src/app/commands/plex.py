"""
Plex command handlers for Discord application.
"""

import logging
from typing import Optional
import discord
from discord import app_commands

from ...integrations.plex_discord import PlexDiscordPlayer
from ..interactions.components import MediaControlView

logger = logging.getLogger(__name__)

class PlexCommands:
    """Plex media commands for Discord application."""
    
    def __init__(self, tree: app_commands.CommandTree, plex_url: str, plex_token: str):
        self.tree = tree
        self.player = PlexDiscordPlayer(tree.client, plex_url, plex_token)
        
    async def initialize(self):
        """Initialize Plex commands and player."""
        await self.player.initialize()
        self._register_commands()
        
    async def cleanup(self):
        """Cleanup resources."""
        await self.player.cleanup()
        
    def _register_commands(self):
        """Register all Plex-related commands."""
        
        @self.tree.command(name="plex-play", description="Play media from Plex")
        @app_commands.describe(
            media_id="The Plex media ID to play",
            quality="Video quality (optional)",
        )
        @app_commands.choices(quality=[
            app_commands.Choice(name="Original", value="original"),
            app_commands.Choice(name="1080p", value="1080"),
            app_commands.Choice(name="720p", value="720"),
            app_commands.Choice(name="480p", value="480"),
        ])
        async def play_media(
            interaction: discord.Interaction, 
            media_id: str, 
            quality: Optional[app_commands.Choice[str]] = None
        ):
            await interaction.response.defer()
            
            try:
                embed = await self.player.create_embed_player(
                    interaction,
                    media_id,
                    quality=quality.value if quality else "original"
                )
                if not embed:
                    await interaction.followup.send("Failed to create media player.")
                    return
                    
                view = MediaControlView(self.player)
                await interaction.followup.send(embed=embed, view=view)
                await self.player.start_playback(interaction)
                
            except Exception as e:
                logger.error(f"Error playing media: {e}")
                await interaction.followup.send(f"Error playing media: {str(e)}")
                
        @self.tree.command(name="plex-search", description="Search for media in Plex")
        @app_commands.describe(
            query="Search term",
            library="Library to search in (optional)",
        )
        async def search_media(
            interaction: discord.Interaction,
            query: str,
            library: Optional[str] = None
        ):
            await interaction.response.defer()
            
            try:
                results = await self.player.search_media(query, library)
                if not results:
                    await interaction.followup.send("No results found.")
                    return
                    
                options = [
                    discord.SelectOption(
                        label=item.title[:100],
                        description=f"{item.type.capitalize()} - {item.year}" if hasattr(item, 'year') else item.type.capitalize(),
                        value=str(item.ratingKey),
                        emoji="🎬" if item.type == "movie" else "📺" if item.type == "episode" else "🎵"
                    )
                    for item in results[:25]
                ]
                
                select = discord.ui.Select(
                    placeholder="Select media to play...",
                    options=options,
                    custom_id="media_select"
                )
                
                async def select_callback(select_interaction: discord.Interaction):
                    await play_media(select_interaction, select_interaction.data["values"][0])
                    
                select.callback = select_callback
                view = discord.ui.View()
                view.add_item(select)
                
                await interaction.followup.send(
                    f"Found {len(results)} results for '{query}':",
                    view=view
                )
                
            except Exception as e:
                logger.error(f"Error searching media: {e}")
                await interaction.followup.send(f"Error searching media: {str(e)}")
                
        @self.tree.command(name="plex-status", description="Show current media playback status")
        async def media_status(interaction: discord.Interaction):
            try:
                state = self.player.get_current_state(str(interaction.guild_id))
                if not state:
                    await interaction.response.send_message("No media currently playing.")
                    return
                    
                embed = discord.Embed(title="Media Status", color=discord.Color.blue())
                embed.add_field(name="Title", value=state.title)
                embed.add_field(
                    name="Position",
                    value=f"{state.position//60}:{state.position%60:02d} / {state.duration//60}:{state.duration%60:02d}"
                )
                embed.add_field(name="Status", value="Playing" if state.is_playing else "Paused")
                embed.set_thumbnail(url=state.thumbnail_url)
                
                progress = int((state.position / state.duration) * 20)
                bar = "▓" * progress + "░" * (20 - progress)
                embed.add_field(name="Progress", value=bar, inline=False)
                
                view = MediaControlView(self.player)
                await interaction.response.send_message(embed=embed, view=view)
                
            except Exception as e:
                logger.error(f"Error getting media status: {e}")
                await interaction.response.send_message(f"Error getting media status: {str(e)}")
                
        @self.tree.command(name="plex-libraries", description="List available Plex libraries")
        async def list_libraries(interaction: discord.Interaction):
            await interaction.response.defer()
            
            try:
                libraries = await self.player.get_libraries()
                
                embed = discord.Embed(
                    title="Plex Libraries",
                    color=discord.Color.blue(),
                    description="Available media libraries:"
                )
                
                for lib in libraries:
                    count = await self.player.get_library_count(lib.key)
                    embed.add_field(
                        name=lib.title,
                        value=f"Type: {lib.type}\nItems: {count:,}",
                        inline=True
                    )
                    
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Error listing libraries: {e}")
                await interaction.followup.send(f"Error listing libraries: {str(e)}") 