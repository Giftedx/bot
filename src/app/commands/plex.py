import logging
import discord
from discord import app_commands
from discord.ext import commands
from src.integrations.plex_player import PlexDiscordPlayer
from src.app.interactions.components import MediaControlView
from typing import Optional

logger = logging.getLogger(__name__)


class PlexSlash(commands.Cog):
    """Plex slash commands (migrated to app_commands)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        plex_url = self.bot.config_manager.get_secret("plex.url")
        plex_token = self.bot.config_manager.get_secret("plex.token")

        if not all([plex_url, plex_token]):
            logger.warning("Plex URL or Token not configured. Plex commands will be unavailable.")
            # We can't raise here, as it would stop the bot.
            # Instead, we can have a check in each command.
            self.player = None
        else:
            self.player = PlexDiscordPlayer(bot, plex_url, plex_token)

    @app_commands.command(name="plex_search", description="Search for media in Plex libraries.")
    @app_commands.describe(query="Search term", library="Library to search in (optional)")
    async def plex_search(self, interaction: discord.Interaction, query: str, library: str = None):
        """Search for media in Plex libraries."""
        if not self.player:
            await interaction.response.send_message("Plex is not configured.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            results = await self.player.search_media(query, library)
            if not results:
                await interaction.followup.send("No results found.")
                return

            options = [
                discord.SelectOption(
                    label=item.title[:100],
                    description=f"{item.type.capitalize()} - {getattr(item, 'year', '')}",
                    value=str(item.ratingKey),
                    emoji="🎬" if item.type == "movie" else "📺" if item.type == "episode" else "🎵",
                )
                for item in results[:25]
            ]

            select = discord.ui.Select(
                placeholder="Select media to play...", options=options, custom_id="media_select"
            )

            async def select_callback(select_interaction: discord.Interaction):
                media_id = select_interaction.data["values"][0]
                await select_interaction.response.defer()

                # Acknowledging the interaction. Now, call the play logic.
                # This requires the `plex_play` command to be migrated and callable.
                # For now, we'll just send a message.
                # TODO: Hook this up to the actual `plex_play` logic once migrated.
                await select_interaction.followup.send(
                    f"Playback for selected media will start shortly.", ephemeral=True
                )

            select.callback = select_callback
            view = discord.ui.View()
            view.add_item(select)

            await interaction.followup.send(
                f"Found {len(results)} results for '{query}':", view=view
            )

        except Exception as e:
            logger.error(f"Error searching media: {e}")
            await interaction.followup.send(f"Error searching media: {str(e)}")

    @app_commands.command(name="plex_play", description="Play media from Plex.")
    @app_commands.describe(
        media_id="The Plex media ID to play",
        quality="Video quality (optional)",
    )
    @app_commands.choices(
        quality=[
            app_commands.Choice(name="Original", value="original"),
            app_commands.Choice(name="1080p", value="1080"),
            app_commands.Choice(name="720p", value="720"),
            app_commands.Choice(name="480p", value="480"),
        ]
    )
    async def plex_play(
        self,
        interaction: discord.Interaction,
        media_id: str,
        quality: Optional[app_commands.Choice[str]] = None,
    ):
        """Plays media from Plex."""
        if not self.player:
            await interaction.response.send_message("Plex is not configured.", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            quality_value = quality.value if quality else "original"
            embed = await self.player.create_embed_player(
                interaction, media_id, quality=quality_value
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

    @app_commands.command(name="plex_libraries", description="List available Plex libraries.")
    async def plex_libraries(self, interaction: discord.Interaction):
        """Lists available Plex libraries."""
        if not self.player:
            await interaction.response.send_message("Plex is not configured.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            libraries = await self.player.get_libraries()

            embed = discord.Embed(
                title="Plex Libraries",
                color=discord.Color.blue(),
                description="Available media libraries:",
            )

            for lib in libraries:
                count = await self.player.get_library_count(lib.key)
                embed.add_field(
                    name=lib.title, value=f"Type: {lib.type}\nItems: {count:,}", inline=True
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error listing libraries: {e}")
            await interaction.followup.send(f"Error listing libraries: {str(e)}")

    @app_commands.command(name="plex_status", description="Show current media playback status.")
    async def plex_status(self, interaction: discord.Interaction):
        """Shows the current Plex playback status."""
        if not self.player:
            await interaction.response.send_message("Plex is not configured.", ephemeral=True)
            return

        try:
            state = self.player.get_current_state(str(interaction.guild_id))
            if not state:
                await interaction.response.send_message(
                    "No media currently playing.", ephemeral=True
                )
                return

            embed = discord.Embed(title="Media Status", color=discord.Color.blue())
            embed.add_field(name="Title", value=state.title)
            embed.add_field(
                name="Position",
                value=f"{state.position//60}:{state.position%60:02d} / {state.duration//60}:{state.duration%60:02d}",
            )
            embed.add_field(name="Status", value="Playing" if state.is_playing else "Paused")
            embed.set_thumbnail(url=state.thumbnail_url)

            progress = int((state.position / state.duration) * 20)
            bar = "▓" * progress + "░" * (20 - progress)
            embed.add_field(name="Progress", value=bar, inline=False)

            view = MediaControlView(self.player)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            logger.error(f"Error getting media status: {e}")
            await interaction.response.send_message(
                f"Error getting media status: {str(e)}", ephemeral=True
            )

    @app_commands.command(name="plex_queue", description="Show the play queue for a Plex client.")
    @app_commands.describe(client_name="Name of the Plex client (optional)")
    async def plex_queue(self, interaction: discord.Interaction, client_name: Optional[str] = None):
        """Shows the play queue for a Plex client."""
        if not self.player:
            await interaction.response.send_message("Plex is not configured.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            if not client_name:
                clients = await self.player.get_clients()
                if not clients:
                    await interaction.followup.send("No active Plex clients found.")
                    return

                embed = discord.Embed(
                    title="Available Plex Clients",
                    description="Please specify a client to see its queue.",
                    color=discord.Color.blue(),
                )
                client_list = "\\n".join([f"- {c.title} ({c.product})" for c in clients])
                embed.add_field(name="Clients", value=client_list)
                await interaction.followup.send(embed=embed)
                return

            play_queue = await self.player.get_play_queue(client_name)
            if not play_queue or not play_queue.items:
                await interaction.followup.send(
                    f"Play queue for '{client_name}' is empty or unavailable."
                )
                return

            embed = discord.Embed(title=f"Play Queue for {client_name}", color=discord.Color.blue())
            queue_text = ""
            for i, item in enumerate(play_queue.items[:15]):
                queue_text += f"**{i+1}.** {item.title}\\n"

            embed.description = queue_text
            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error getting play queue: {e}")
            await interaction.followup.send(f"Error getting play queue: {str(e)}")

    @app_commands.command(name="plex_next", description="Skip to the next item for a Plex client.")
    @app_commands.describe(client_name="Name of the Plex client")
    async def plex_next(self, interaction: discord.Interaction, client_name: str):
        """Skips to the next item."""
        if not self.player:
            await interaction.response.send_message("Plex is not configured.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        try:
            success = await self.player.skip_next(client_name)
            if success:
                await interaction.followup.send(f"Skipped to the next item on '{client_name}'.")
        except Exception as e:
            logger.error(f"Error skipping to next item: {e}")
            await interaction.followup.send(f"Error skipping to next item: {str(e)}")

    @app_commands.command(
        name="plex_previous", description="Go to the previous item for a Plex client."
    )
    @app_commands.describe(client_name="Name of the Plex client")
    async def plex_previous(self, interaction: discord.Interaction, client_name: str):
        """Goes to the previous item."""
        if not self.player:
            await interaction.response.send_message("Plex is not configured.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        try:
            success = await self.player.skip_previous(client_name)
            if success:
                await interaction.followup.send(f"Skipped to the previous item on '{client_name}'.")
        except Exception as e:
            logger.error(f"Error skipping to previous item: {e}")
            await interaction.followup.send(f"Error skipping to previous item: {str(e)}")

    @app_commands.command(name="plex_pause", description="Pause the current media playback.")
    async def plex_pause(self, interaction: discord.Interaction):
        """Pauses the current media playback."""
        if not self.player:
            await interaction.response.send_message("Plex is not configured.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        try:
            await self.player.pause_playback(interaction)
            await interaction.followup.send("Playback paused.")
        except Exception as e:
            logger.error(f"Error pausing playback: {e}")
            await interaction.followup.send(f"Error pausing playback: {str(e)}")

    @app_commands.command(name="plex_resume", description="Resume the current media playback.")
    async def plex_resume(self, interaction: discord.Interaction):
        """Resumes the current media playback."""
        if not self.player:
            await interaction.response.send_message("Plex is not configured.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        try:
            await self.player.resume_playback(interaction)
            await interaction.followup.send("Playback resumed.")
        except Exception as e:
            logger.error(f"Error resuming playback: {e}")
            await interaction.followup.send(f"Error resuming playback: {str(e)}")

    @app_commands.command(name="plex_stop", description="Stop the current media playback.")
    async def plex_stop(self, interaction: discord.Interaction):
        """Stops the current media playback."""
        if not self.player:
            await interaction.response.send_message("Plex is not configured.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        try:
            await self.player.stop_playback(interaction)
            await interaction.followup.send("Playback stopped.")
        except Exception as e:
            logger.error(f"Error stopping playback: {e}")
            await interaction.followup.send(f"Error stopping playback: {str(e)}")


async def setup(bot: commands.Bot):
    await bot.add_cog(PlexSlash(bot))
