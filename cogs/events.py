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
        bots = sum(m.bot for m in guild.members)
        humans = guild.member_count - bots
        
        await self.bot.change_presence(
            activity=discord.Activity(
                type=config.ACTIVITY_TYPE,
                name=f"{humans:,d} + {bots} üyeyi",
            ),
            status=config.STATUS_TYPE,
        )

    @commands.Cog.listener()
    async def on_ready(self):
        if not hasattr(self, "uptime"):
            self.bot.uptime = datetime.datetime.now()

        print(
            f"{self.bot.user} (ID: {self.bot.user.id})\n"
            f"discord.py version: {discord.__version__}"
        )

        await self._change_presence()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self._change_presence()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self._change_presence()
