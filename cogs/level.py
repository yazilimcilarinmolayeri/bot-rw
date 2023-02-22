import discord
from discord.ext import commands

from utils import models


async def setup(bot):
    await bot.add_cog(Level(bot))


class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.DEFAULT_AMOUNT = 10
        self.CATEGORY_ID = bot.config["level"]["category_id"]

    async def _update_xp(self, message: discord.Message, amount: int):
        guild_id = message.guild.id
        member_id = message.author.id

        stat = await models.LevelStat.get_or_none(
            guild_id=guild_id, member_id=member_id
        )

        if stat is None:
            return await models.LevelStat.create(
                guild_id=guild_id,
                member_id=member_id,
                xp=amount,
            )

        if stat.ignore:
            return

        new_xp = stat.xp + amount
        new_level = int(new_xp ** (1 / 5))

        if new_level > stat.level:
            self.bot.dispatch("level_up", message, new_level)

        stat.xp = new_xp
        stat.level = new_level
        await stat.save()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # if message.channel in message.guild.get_channel(self.CATEGORY_ID):
        await self._update_xp(message, self.DEFAULT_AMOUNT)

    @commands.Cog.listener()
    async def on_level_up(self, message, level):
        await message.channel.send(
            f"{message.author.mention}, has leveled up to level `{level}`!"
        )

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(moderate_members=True)
    async def ignore(self, ctx: commands.Context, member: discord.Member = None):
        """Ignore a member level system."""

        pass

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(moderate_members=True)
    async def delxp(
        self, ctx: commands.Context, member: discord.Member = None, amount: int = -10
    ):
        """Remove a member xp."""

        pass

    @commands.guild_only()
    @commands.command(aliases=["level"])
    async def rank(self, ctx: commands.Context, member: discord.Member = None):
        """Show a member rank stats."""

        member = member or ctx.author
        stat = await models.LevelStat.get_or_none(
            guild_id=ctx.guild.id, member_id=member.id
        )

        if stat is None:
            return await ctx.send("Rank not found!")

        min_xp = stat.level**5
        next_level_xp = (stat.level + 1) ** 5
        xp_required = next_level_xp - min_xp
        xp_have = stat.xp - min_xp
        percentage = round((xp_have * 100) / xp_required)

        filled_length = int(25 * percentage // 100)
        bar = "▓" * filled_length + "░" * (25 - filled_length)

        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_author(name=member.name, icon_url=member.display_avatar.url)
        embed.description = (
            f"Level: `{stat.level}` Position: `?` "
            f"XP: `{stat.xp:,}`/`{next_level_xp:,}`\n"
            f"```[{bar}] {percentage}%```".replace(",", ".")
        )
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(aliases=["lb"])
    async def leaderboard(self, ctx: commands.Context):
        """Show the guild leaderboard."""

        pass
