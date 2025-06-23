import discord
from discord.ext import commands
import asyncio


class Activities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="activity")
    async def start_activity(self, ctx, activity_type: str = None):
        """Start a Discord Activity in the voice channel"""
        if not ctx.author.voice:
            return await ctx.send("You need to be in a voice channel!")

        # Dictionary of available activities and their corresponding IDs
        activities = {
            "youtube": "880218394199220334",  # Watch Together
            "poker": "755827207812677713",  # Poker Night
            "betrayal": "773336526917861400",  # Betrayal.io
            "fishing": "814288819477020702",  # Fishington.io
            "chess": "832012774040141894",  # Chess in the Park
            "letter": "879863686565621790",  # Letter League
            "word": "879863976006127627",  # Word Snacks
            "sketch": "902271654783242291",  # Sketch Heads
            "spellcast": "852509694341283871",  # Spellcast
        }

        if not activity_type:
            # Show available activities
            activity_list = "\n".join(f"• {name}" for name in activities.keys())
            embed = discord.Embed(
                title="Available Activities",
                description=f"Use `!activity <name>` to start an activity:\n{activity_list}",
                color=discord.Color.blue(),
            )
            return await ctx.send(embed=embed)

        activity_type = activity_type.lower()
        if activity_type not in activities:
            return await ctx.send(f"Invalid activity! Use `!activity` to see available options.")

        try:
            # Create invite with activity
            invite = await ctx.author.voice.channel.create_invite(
                target_type=discord.InviteTarget.embedded_application,
                target_application_id=activities[activity_type],
                max_age=3600,  # 1 hour
            )

            embed = discord.Embed(
                title=f"Discord Activity: {activity_type.title()}",
                description=f"Click the link below to join the activity!\n{invite.url}",
                color=discord.Color.green(),
            )
            await ctx.send(embed=embed)

        except discord.Forbidden:
            await ctx.send("I don't have permission to create invites for this channel!")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")


async def setup(bot):
    await bot.add_cog(Activities(bot))
