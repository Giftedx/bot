"""Utility functions for Discord bot interactions."""

import logging
import discord
from discord.ext import commands
from typing import Union, Optional

logger = logging.getLogger(__name__)


async def update_status(
    ctx_or_interaction: Union[commands.Context, discord.Interaction],
    message: str,
    ephemeral: bool = False,
    embed: Optional[discord.Embed] = None,
    view: Optional[discord.ui.View] = None,
) -> Optional[Union[discord.Message, discord.WebhookMessage]]:
    """
    Sends or responds to a command/interaction with a message.
    Handles both regular commands.Context and slash command discord.Interaction.
    For interactions, it manages initial response vs. followup.

    Args:
        ctx_or_interaction: The context or interaction object.
        message: The message content to send.
        ephemeral: Whether the message should be ephemeral (for interactions only).
        embed: An optional embed to send with the message.
        view: An optional view to send with the message.

    Returns:
        The sent discord.Message or discord.WebhookMessage, or None if sending failed.
    """
    sent_message: Optional[Union[discord.Message, discord.WebhookMessage]] = None
    try:
        if isinstance(ctx_or_interaction, discord.Interaction):
            if not ctx_or_interaction.response.is_done():
                logger.debug(f"Sending initial response to interaction ID: {ctx_or_interaction.id}")
                await ctx_or_interaction.response.send_message(
                    content=message, embed=embed, view=view, ephemeral=ephemeral
                )
                # For initial responses, to get the message object, we'd need to use followup if we want to return it,
                # or handle it differently if interaction.response.send_message doesn't return what we need.
                # However, the primary goal is to send. If a message object is needed, followup is more consistent.
                # For simplicity here, we assume send_message is enough and followup will give us the WebhookMessage.
                # If we need the actual Message, for an initial response, it's tricky without followup.
                # Let's assume for now that if an initial response is made, getting the message object
                # is less critical than just sending it. If we *must* return it, we might prefer followup.
                # A common pattern for initial response is to send, then use followup to edit or get the message.
                # For now, if it's an initial response, we won't fetch the message object directly from send_message.
                # We will try to get it via original_response() if possible, or use followup for explicit message return.
                if ephemeral:  # Cannot get original response for ephemeral messages easily
                    sent_message = None
                else:
                    try:
                        sent_message = await ctx_or_interaction.original_response()
                    except (
                        discord.errors.NotFound
                    ):  # If response was already sent via followup or other means
                        logger.debug(
                            f"Could not fetch original_response for interaction {ctx_or_interaction.id}, using followup."
                        )
                        sent_message = await ctx_or_interaction.followup.send(
                            content=message, embed=embed, view=view, ephemeral=ephemeral
                        )
            else:
                logger.debug(f"Sending followup message to interaction ID: {ctx_or_interaction.id}")
                sent_message = await ctx_or_interaction.followup.send(
                    content=message, embed=embed, view=view, ephemeral=ephemeral
                )
        elif isinstance(ctx_or_interaction, commands.Context):
            logger.debug(f"Sending message to context for command: {ctx_or_interaction.command}")
            sent_message = await ctx_or_interaction.send(content=message, embed=embed, view=view)
        else:
            logger.error(
                f"Invalid context/interaction type provided to update_status: {type(ctx_or_interaction)}"
            )
            return None

        return sent_message

    except discord.errors.HTTPException as e:
        logger.error(
            f"Discord HTTP error sending status update: {e.status} - {e.text}", exc_info=True
        )
        return None
    except Exception as e:
        logger.error(f"Unexpected error sending status update: {e}", exc_info=True)
        return None
