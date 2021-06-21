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

    def get_emoji(self, guild, emoji_id):
        emoji = discord.utils.get(guild.emojis, id=emoji_id)

        try:
            if emoji.animated:
                return "<a:{}:{}>".format(emoji.name, emoji.id)
            else:
                return "<:{}:{}>".format(emoji.name, emoji.id)
        except AttributeError:
            return False

    async def show_help(self, command=None):
        cmd = self.bot.get_command("help")
        command = command or self.command.qualified_name

        await self.invoke(cmd, command=command)
