#!/usr/bin/python3

import os
import asyncio
import logging
import logging.handlers

import yaml
import discord
from discord.ext import commands
from aiohttp import ClientSession

from utils import context


class Bot(commands.Bot):
    def __init__(
        self,
        *args,
        config,
        web_client: ClientSession,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.config = config
        self.web_client = web_client
        self.embed_color = config["general"]["embed_color"]
        self.initial_extensions = config["general"]["initial_extensions"]

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

    async with ClientSession() as web_client:
        with open("config.yml", "r", encoding="UTF-8") as file:
            config = yaml.safe_load(file)

        async with Bot(
            config=config,
            web_client=web_client,
            intents=discord.Intents.all(),
            command_prefix=config["general"]["prefixs"],
            owner_ids=set([id for id in config["general"]["owner_ids"]]),
        ) as bot:
            await bot.start(token=config["general"]["token"])


if __name__ == "__main__":
    asyncio.run(main())
