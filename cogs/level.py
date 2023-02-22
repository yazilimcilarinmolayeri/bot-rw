import discord
from discord.ext import commands, menus

from utils import constant, models
from utils.paginator import DescriptionSource


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

        stat = await models.LevelStat.get_or_none(guild_id=guild_id, member_id=member_id)

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

        if message.channel in message.guild.get_channel(self.CATEGORY_ID).channels:
            await self._update_xp(message, self.DEFAULT_AMOUNT)

    @commands.Cog.listener()
    async def on_level_up(self, message, level):
        # await message.channel.send(
        #     f"{message.author.mention}, has leveled up to level `{level}`!"
        # )

        pass

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
            f"LVL: `{stat.level}` XP: `{stat.xp:,}`/`{next_level_xp:,}`\n"
            f"```[{bar}] {percentage}%```".replace(",", ".")
        )
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(aliases=["lb"])
    async def leaderboard(self, ctx: commands.Context):
        """Show the guild leaderboard."""

        entries = []
        stat = await models.LevelStat.filter(guild_id=ctx.guild.id).order_by("-level")

        for i, s in enumerate(stat):
            member = ctx.guild.get_member(s.member_id)
            mention = f"<@{s.member_id}>" if member is None else member.mention
            entries.append(
                f"`{i + 1}` - {mention} "
                f"`{s.level} LVL | {s.xp:,} XP`\n".replace(",", ".")
            )

        menu = menus.MenuPages(
            DescriptionSource(entries, title="Leadboard", per_page=30),
            clear_reactions_after=True,
        )
        await menu.start(ctx)

    @commands.is_owner()
    @commands.command(hidden=True)
    async def loadxp(self, ctx: commands.Context, category_id: int):
        """Load member xp's from category channels to database."""

        category = ctx.guild.get_channel(category_id)

        for channel in category.channels:
            if not isinstance(channel, discord.TextChannel):
                continue

            log_message = await ctx.send(
                f"Loading {channel.mention} {constant.Emoji.loading}"
            )

            async for message in channel.history(oldest_first=True, limit=None):
                if message.author.bot:
                    continue
                if message.author.discriminator == "0000":
                    continue

                await self._update_xp(message, amount=self.DEFAULT_AMOUNT)
            await log_message.edit(content=f"Done {channel.mention}")
        await ctx.send("All done!")
