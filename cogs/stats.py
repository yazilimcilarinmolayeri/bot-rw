import discord
from tortoise.query_utils import Q
from tortoise.functions import Sum
from discord.ext import commands, menus

from utils import paginator, models, functions, time as util_time


async def setup(bot):
    await bot.add_cog(Stats(bot))


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_emoji_stats(self, ctx, data, key="amount"):
        check_emoji = lambda emoji: "\U0001f5d1" if not emoji else emoji

        stats = "\n".join(
            [
                "{} `{} (En son: {})`".format(
                    check_emoji(ctx.get_emoji(ctx.guild, d["emoji_id"])),
                    d[key],
                    util_time.humanize(d["last_usage"]),
                )
                for d in data
            ]
        )

        return stats

    @commands.group(invoke_without_command=True, aliases=["es"])
    async def emojistats(self, ctx, member: discord.Member = None):
        """Shows you statistics about the emoji usage on author."""

        embeds = []
        guild = ctx.guild

        if member == None:
            member = ctx.author

        data = (
            await models.EmojiUsageStat.filter(
                Q(guild_id=guild.id) & Q(user_id=member.id)
            )
            .order_by("-amount")
            .values("emoji_id", "amount", "last_usage")
        )
        total = sum([d["amount"] for d in data])

        for data in functions.list_to_matrix(data):
            embed = discord.Embed(color=self.bot.color)
            embed.set_author(name=member, icon_url=member.avatar.url)
            embed.description = "{}\n\n{}".format(
                self.get_emoji_stats(ctx, data),
                "Toplam: `{}`".format(total),
            )
            embeds.append(embed)

        menu = menus.MenuPages(
            timeout=30,
            clear_reactions_after=True,
            source=paginator.EmbedSource(data=embeds),
        )
        try:
            await menu.start(ctx)
        except IndexError:
            await ctx.send("Kayıt bulunamadı!")

    @emojistats.command(name="server", aliases=["s"])
    async def emojistats_server(self, ctx):
        """Shows statistics about the emoji usage on server."""

        embeds = []
        guild = ctx.guild
        get_member = lambda member_id: guild.get_member(member_id)

        data = (
            await models.EmojiUsageStat.filter(guild_id=guild.id)
            .annotate(sum=Sum("amount"))
            .group_by("emoji_id")
            .order_by("-sum")
            .values()
        )

        last_usage = (
            await models.EmojiUsageStat.filter(guild_id=guild.id)
            .order_by("-last_usage")
            .limit(1)
            .values()
        )

        last_usage = last_usage[0]

        for data in functions.list_to_matrix(data):
            emoji = ctx.get_emoji(ctx.guild, last_usage["emoji_id"])

            if not emoji:
                emoji = "\U0001f5d1"

            embed = discord.Embed(color=self.bot.color)
            embed.set_author(name=guild, icon_url=guild.icon.url)
            embed.description = "{}\n\nEn son: {}".format(
                self.get_emoji_stats(ctx, data, key="sum"),
                "{} {} `({})`".format(
                    emoji,
                    get_member(last_usage["user_id"]).mention,
                    util_time.humanize(last_usage["last_usage"]),
                ),
            )
            embeds.append(embed)

        menu = menus.MenuPages(
            timeout=30,
            clear_reactions_after=True,
            source=paginator.EmbedSource(data=embeds),
        )
        try:
            await menu.start(ctx)
        except IndexError:
            await ctx.send("Kayıt bulunamadı!")
