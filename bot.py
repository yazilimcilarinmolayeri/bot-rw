#!/usr/bin/python3

#
# Copyright (C) 2020-2022 yazilimcilarinmolayeri
#

import os
import json
import logging
import warnings

import discord
import aiohttp
from discord.ext import commands

from utils import context


extensions = (
    "jishaku",
    "cogs.api",
    "cogs.events",
    "cogs.feed",
    "cogs.info",
    "cogs.owner",
    "cogs.reactionrole",
    "cogs.stats",
    "cogs.utility",
)

os.environ["JISHAKU_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"


class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = config
        self.color = 0x2F3136
        self.session = aiohttp.ClientSession()

        for cog in extensions:
            try:
                self.load_extension(cog)
            except Exception as exc:
                print(f"{cog} {exc.__class__.__name__}: {exc}")

    @property
    def owners(self):
        return [self.get_user(id) for id in self.owner_ids]

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
        super().run(self.config["bot"]["token"], reconnect=True)


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    logger = logging.getLogger("discord")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(filename="bot.log", mode="w", encoding="utf-8")
    formatter = logging.Formatter(
        "[%(asctime)s][%(levelname)s][%(name)s] - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    with open("config.json") as file:
        config = json.loads(file.read())

    bot = MyBot(
        config=config,
        intents=discord.Intents.all(),
        command_prefix=config["bot"]["command_prefix"],
        owner_ids=set(config["bot"]["owner_ids"]),
    )
    bot.run()
