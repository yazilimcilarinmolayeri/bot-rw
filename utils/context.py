# -*- coding: utf-8 -*-

import discord
from utils import lists
from discord.ext import commands


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.symbols = lists.symbols

    def __repr__(self):
        return "<Context>"

    def _format(self, emoji, content):
        return "{} | {}".format(emoji, content)

    def get_emoji(self, guild, emoji_id):
        emoji = discord.utils.get(guild.emojis, id=emoji_id)

        if emoji.animated:
            return "<a:{}:{}>".format(emoji.name, emoji.id)
        else:
            return "<:{}:{}>".format(emoji.name, emoji.id)

    async def info(self, content):
        emoji = self.symbols.get("info")
        await self.send(self._format(emoji, content))

    async def success(self, content):
        emoji = self.symbols.get("success")
        await self.send(self._format(emoji, content))

    async def warning(self, content):
        emoji = self.symbols.get("warning")
        await self.send(self._format(emoji, content))

    async def error(self, content):
        emoji = self.symbols.get("error")
        await self.send(self._format(emoji, content))

    async def loading(self, content):
        emoji = self.symbols.get("loading")
        await self.send(self._format(emoji, content))

    async def link(self, content):
        emoji = self.symbols.get("link")
        await self.send(self._format(emoji, content))

    async def show_help(self, command=None):
        cmd = self.bot.get_command("help")
        command = command or self.command.qualified_name

        await self.invoke(cmd, command=command)
