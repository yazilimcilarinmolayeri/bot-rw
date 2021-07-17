# -*- coding: utf-8 -*-

import discord
from discord.ext import commands
from utils import lists, time as util_time


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.symbols = lists.symbols

    def __repr__(self):
        return "<Context>"

    def get_emoji(self, guild, id):
        emoji = discord.utils.get(guild.emojis, id=id)

        try:
            if emoji.animated:
                return "<a:{}:{}>".format(emoji.name, emoji.id)
            else:
                return "<:{}:{}>".format(emoji.name, emoji.id)
        except AttributeError:
            return False

    def format_relative(self, dt):
        return util_time.format_dt(dt, "R")

    def format_date(self, dt):
        if dt is None:
            return "?"

        return "{} ({})".format(
            util_time.format_dt(dt, "F"), self.format_relative(dt)
        )

    async def show_help(self, command=None):
        cmd = self.bot.get_command("help")
        command = command or self.command.qualified_name

        await self.invoke(cmd, command=command)
