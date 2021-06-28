#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Copyright (C) 2020-2021 yazilimcilarinmolayeri

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import aiohttp
import discord
import warnings
import configparser
from utils import context
from discord.ext import commands


description = """
    Hello! I am a multifunctional Discord bot (ymybot rewrite version).
"""

extensions = (
    "jishaku",
    "cogs.api",
    "cogs.events",
    "cogs.feed",
    "cogs.info",
    "cogs.owner",
    "cogs.stats",
    "cogs.utility",
)


def _get_config():
    config = configparser.ConfigParser()
    files = config.read("config.cfg")

    if not len(files):
        print("Config file not found!")
        exit()

    return config


def _prefix_callable(bot, msg):
    user_id = bot.user.id
    base = config.get("Bot", "PREFIX").split(",")
    base.extend(["<@!{}> ".format(user_id), "<@{}> ".format(user_id)])

    return base


config = _get_config()
warnings.filterwarnings("ignore", category=DeprecationWarning)


class YMYRWBot(commands.Bot):
    def __init__(self):
        super().__init__(
            description=description,
            intents=discord.Intents.all(),  # New in version 1.5
            command_prefix=_prefix_callable,
            owner_ids=set(
                [int(id) for id in config.get("Bot", "OWNER_IDS").split(",")]
            ),
        )

        self.uptime = ""
        self.config = config
        self.color = 0x2F3136
        self.session = aiohttp.ClientSession(loop=self.loop)

        for cog in extensions:
            try:
                self.load_extension(cog)
            except Exception as exc:
                print("{} {}: {}".format(cog, exc.__class__.__name__, exc))

    @property
    def __version__(self):
        return "0.50.20"

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
        super().run(self.config.get("Bot", "TOKEN"), reconnect=True)


if __name__ == "__main__":
    bot = YMYRWBot()
    bot.run()
