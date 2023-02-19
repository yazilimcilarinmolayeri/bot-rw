from datetime import datetime

import discord
from discord.utils import format_dt
from discord.ext import commands, menus
from tortoise.functions import Sum
from tortoise.expressions import Q, F

from utils import paginator, models, functions


async def setup(bot):
    await bot.add_cog(Stats(bot))


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def update_emoji_stats(self, message):
        guild_id = message.guild.id
        user_id = message.author.id
        emojis = functions.get_message_emojis(message)

        for emoji, total in emojis.items():
            emoji_stats = await models.EmojiStats.get_or_none(
                guild_id=guild_id, user_id=user_id, emoji_id=emoji.id
            )

            if emoji_stats is None:
                await models.EmojiStats.create(
                    guild_id=guild_id,
                    user_id=user_id,
                    emoji_id=emoji.id,
                    total=total,
                    last=datetime.utcnow(),
                )
            else:
                emoji_stats.total = F("total") + total
                emoji_stats.last = datetime.utcnow()
                await emoji_stats.save()

    @commands.Cog.listener(name="on_message")
    async def on_message_emoji(self, message):

        if message.author.bot:
            return

        await self.update_emoji_stats(message)

    @commands.group(invoke_without_command=True, aliases=["es"])
    async def emojistats(self, ctx, user: discord.Member = None):
        """Shows you statistics about the emoji usage on member."""

        entries = []

        if user is None:
            user = ctx.author

        emoji_stats = await models.EmojiStats.filter(
            guild_id=ctx.guild.id, user_id=user.id
        ).order_by("-total")

        if not emoji_stats:
            return await ctx.send("Stats not found.")

        for stats in emoji_stats:
            try:
                emoji = await ctx.guild.fetch_emoji(stats.emoji_id)
            except discord.errors.NotFound:
                emoji = "*removed*"

            last = format_dt(stats.last, style="R")
            entries.append(f"{emoji} - `{stats.total}` Last: {last}\n")

        menu = menus.MenuPages(
            paginator.PageSource(entries, per_page=10), clear_reactions_after=True
        )
        await menu.start(ctx)

    @emojistats.command(name="server", aliases=["s"])
    async def emojistats_server(self, ctx):
        """Shows statistics about the emoji usage on server."""

        entries = []

        emoji_stats = (
            await models.EmojiStats.filter(guild_id=ctx.guild.id)
            .group_by("emoji_id")
            .order_by("-total")
        )

        """
        last = (
            await models.EmojiStats.filter(guild_id=guild.id)
            .order_by("-last")
            .limit(1)
            .values()
        )
        """

        if not emoji_stats:
            return await ctx.send("Stats not found.")

        for stats in emoji_stats:
            try:
                emoji = await ctx.guild.fetch_emoji(stats.emoji_id)
            except discord.errors.NotFound:
                emoji = "*removed*"

            last = format_dt(stats.last, style="R")
            entries.append(f"{emoji} - `{stats.total}` Last: {last}\n")

        menu = menus.MenuPages(
            paginator.PageSource(entries, per_page=10), clear_reactions_after=True
        )
        await menu.start(ctx)
