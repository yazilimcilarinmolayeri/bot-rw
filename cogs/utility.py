# -*- coding: utf-8 -*-

import os
import time
import inspect
import discord
from discord.ext import commands


def setup(bot):
    bot.add_cog(Utility(bot))


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["u"])
    async def uptime(self, ctx):
        """"""

        await ctx.send(
            "Uptime: `{}`".format(
                self.bot.uptime.strftime("%H:%M:%S %d.%m.%Y")
            )
        )

    @commands.command(aliases=["p"])
    async def ping(self, ctx):
        """"""

        before = time.monotonic()
        message = await ctx.send("Pinging...")
        ping = (time.monotonic() - before) * 1000

        await message.edit(content="Pong! `{}ms`".format(round(ping, 2)))

    @commands.command(aliases=["kaynak"])
    async def source(self, ctx, *, command=None):
        """"""

        branch = "main"
        source_url = "https://github.com/yazilimcilarinmolayeri/rtfm-bot"

        if command is None:
            return await ctx.send(source_url)

        if command == "help":
            src = type(self.bot.help_command)
            module = src.__module__
            filename = inspect.getsourcefile(src)
        else:
            obj = self.bot.get_command(command.replace(".", " "))

            if obj is None:
                return await ctx.send("Komut bulunamadı!")

            src = obj.callback.__code__
            module = obj.callback.__module__
            filename = src.co_filename

        lines, firstlineno = inspect.getsourcelines(src)
        location = os.path.relpath(filename).replace("\\", "/")
        final_url = "<{}/blob/{}/{}#L{}-L{}>".format(
            source_url,
            branch,
            location,
            firstlineno,
            firstlineno + len(lines) - 1,
        )

        await ctx.send(final_url)
