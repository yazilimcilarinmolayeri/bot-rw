#!/usr/bin/python3

import os
import asyncio
import logging
import configparser
import logging.handlers
from typing import List

import discord
from discord.ext import commands
from aiohttp import ClientSession

from utils import context


class Bot(commands.Bot):
    def __init__(
        self,
        *args,
        config: configparser.ConfigParser,
        embed_color: int,
        web_client: ClientSession,
        initial_extensions: List[str],
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.config = config
        self.embed_color = embed_color
        self.web_client = web_client
        self.initial_extensions = initial_extensions

    async def setup_hook(self):
        for extension in self.initial_extensions:
            await self.load_extension(extension)

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=context.Context)

        if ctx.command is None:
            return

        await self.invoke(ctx)

    async def on_message(self, message):
        if message.author.bot:
            return

        await self.process_commands(message)


async def main():
    os.environ["JISHAKU_UNDERSCORE"] = "True"
    os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"

    logger = logging.getLogger("discord")
    logger.setLevel(logging.INFO)

    handler = logging.handlers.RotatingFileHandler(
        backupCount=5,
        encoding="utf-8",
        maxBytes=32 * 1024 * 1024,
        filename="discord.log",
    )
    formatter = logging.Formatter(
        "[{asctime}] [{levelname}] {name}: {message}", style="{"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    async with ClientSession() as our_client:
        embed_color = 0x2F3136
        initial_extensions = [
            "jishaku",
            "cogs.api",
            "cogs.events",
            "cogs.info",
            "cogs.owner",
            "cogs.reactionrole",
            "cogs.utility",
        ]
        intents = discord.Intents.all()

        config = configparser.ConfigParser()
        config.read("config.ini")

        token = config.get("bot", "token")
        command_prefix = config.get("bot", "command_prefix").split(",")
        owner_ids = set([int(id) for id in config.get("bot", "owner_ids").split(",")])

        async with Bot(
            config=config,
            embed_color=embed_color,
            web_client=our_client,
            initial_extensions=initial_extensions,
            intents=intents,
            command_prefix=command_prefix,
            owner_ids=owner_ids,
        ) as bot:
            await bot.start(token=token)


asyncio.run(main())
