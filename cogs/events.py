# -*- coding: utf-8 -*-

import discord
import datetime
from utils import config
from discord.ext import commands


def setup(bot):
    bot.add_cog(Events(bot))


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _change_presence(self):
        guild = self.bot.get_guild(config.DEFAULT_GUILD_ID)

        # 1,234 üyeyi izliyor
        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{guild.member_count:,d} üyeyi",
            ),
            status=discord.Status.idle,
        )

    @commands.Cog.listener()
    async def on_ready(self):
        if not hasattr(self, "uptime"):
            self.bot.uptime = datetime.datetime.now()

        print(
            f"discord.py version: {discord.__version__}\n"
            f"{self.bot.user} (ID: {self.bot.user.id})"
        )

        await self._change_presence()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self._change_presence()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self._change_presence()
