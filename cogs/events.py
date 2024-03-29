import logging
import traceback
from io import StringIO
from datetime import datetime

import discord
from discord.ext import commands, menus

from utils import models


logger = logging.getLogger("discord")


async def setup(bot):
    await bot.add_cog(Events(bot))


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ERROR_CHANNEL = bot.get_channel(self.bot.config["log"]["error_channel_id"])

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.launch_time = datetime.utcnow()
        logger.info(f"{self.bot.user} is running!")

        await models.database_init()

        activity = discord.Activity(type=discord.ActivityType.watching, name="👀")
        await self.bot.change_presence(activity=activity)

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(
            error,
            (
                menus.MenuError,
                discord.Forbidden,
                commands.CommandNotFound,
                commands.DisabledCommand,
                discord.errors.HTTPException,
            ),
        ):
            return

        if isinstance(error, commands.errors.CommandOnCooldown):
            return await ctx.send(
                f"Wait `{round(error.retry_after)}` seconds to use it again."
            )

        if isinstance(error, commands.errors.MissingRequiredArgument):
            return await ctx.send(error)  # TODO: Better format output

        if isinstance(error, commands.errors.BadArgument):
            return await ctx.send(str(error).replace('"', "`"))

        if isinstance(error, commands.CheckFailure):
            return await ctx.message.add_reaction("\N{NO ENTRY SIGN}")

        error = error.original
        exc = "".join(
            traceback.format_exception(
                type(error), error, error.__traceback__, chain=False
            )
        )
        await ctx.message.add_reaction("\N{EXCLAMATION QUESTION MARK}")
        await self.ERROR_CHANNEL.send(
            content=(
                f"In `{ctx.command.qualified_name}`: "
                f"`{error.__class__.__name__}`: `{error}`"
            ),
            file=discord.File(
                StringIO(exc),
                filename="traceback.txt",
            ),
        )
