#!/usr/bin/python3
# -*- coding: utf-8 -*-

import aiohttp
import discord
import warnings
from discord.ext import commands
from utils import config, database, context


EXTENSIONS = [
    "jishaku",
    "cogs.api",
    "cogs.events",
    "cogs.info",
    "cogs.owner",
    "cogs.utility",
]

intents = discord.Intents.all()  # New in version 1.5
warnings.filterwarnings("ignore", category=DeprecationWarning)


class YMYBOT(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=config.PREFIX, intents=intents)

        self.uptime = ""
        self.color = 0x2F3136
        self.db = database.Database("database")
        self.session = aiohttp.ClientSession(loop=self.loop)

        for cog in EXTENSIONS:
            try:
                self.load_extension(cog)
            except Exception as exc:
                print("{} {}: {}".format(cog, exc.__class__.__name__, exc))

    @property
    def __version__(self):
        return "0.24.9"

    async def on_resumed(self):
        print("Resumed...")

    async def on_message(self, message):
        if message.author.bot:
            return

        await self.process_commands(message)

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=context.Context)

        if ctx.command is None:
            return

        await self.invoke(ctx)

    async def close(self):
        await super().close()
        await self.session.close()

    def run(self):
        super().run(config.TOKEN, reconnect=True)


if __name__ == "__main__":
    YMYBOT().run()