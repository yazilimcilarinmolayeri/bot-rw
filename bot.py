# -*- coding: utf-8 -*-

import aiohttp
import discord
import warnings
from utils import config
from discord.ext import commands


intents = discord.Intents.all()  # New in version 1.5
warnings.filterwarnings("ignore", category=DeprecationWarning)

EXTENSIONS = [
    "jishaku",
    "cogs.api",
    "cogs.events"
]


class YMYBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=config.PREFIX, intents=intents)

        self.uptime = ""
        self.color = 0x2F3136
        # self.color = discord.Colour.dark_theme()
        self.session = aiohttp.ClientSession(loop=self.loop)

        for cog in EXTENSIONS:
            try:
                self.load_extension(cog)
            except Exception as exc:
                print(f"{cog} {exc.__class__.__name__}: {exc}")

    async def on_resumed(self):
        print("Resumed...")

    async def close(self):
        await super().close()
        await self.session.close()

    def run(self):
        super().run(cofig.TOKEN, reconnect=True)
