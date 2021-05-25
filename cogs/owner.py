# -*- coding: utf-8 -*-

import copy
from discord.ext import commands
from jishaku.codeblocks import codeblock_converter


def setup(bot):
    bot.add_cog(Owner(bot))


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.command(aliases=["r"])
    async def reload(self, ctx):
        """Reloads the given extension names."""

        command = self.bot.get_command("jsk reload")
        await command.__call__(ctx, list(self.bot.extensions.keys()))

    @commands.is_owner()
    @commands.command(aliases=["sh", "s"])
    async def shell(self, ctx, *, codeblock: codeblock_converter):
        """Executes statements in the system shell."""

        command = self.bot.get_command("jsk shell")
        await command.__call__(ctx, argument=codeblock)

    @commands.command()
    @commands.is_owner()
    async def do(self, ctx, times, *, command):
        """Runs a command multiple times in a row."""

        message = copy.copy(ctx.message)
        message.content = ctx.prefix + command

        new_ctx = await self.bot.get_context(message, cls=type(ctx))

        for i in range(int(times)):
            await new_ctx.reinvoke()
