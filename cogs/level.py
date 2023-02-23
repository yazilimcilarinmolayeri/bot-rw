import discord
from discord.ext import commands, menus

from utils import constant, models
from utils.paginator import DescriptionSource


async def setup(bot):
    await bot.add_cog(Level(bot))


class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.AMOUNT = bot.config["level"]["amount"]
        self.CATEGORY_ID = bot.config["level"]["category_id"]

    async def _update_xp(self, message: discord.Message, member_id: int, amount: int):
        guild_id = message.guild.id
        levelstat = await models.LevelStat.get_or_none(
            guild_id=guild_id, member_id=member_id
        )

        if levelstat is None:
            return await models.LevelStat.create(
                guild_id=guild_id,
                member_id=member_id,
                xp=amount,
            )

        new_xp = levelstat.xp + amount
        new_level = int(new_xp ** (1 / 5))

        if new_level > levelstat.level:
            self.bot.dispatch("level_up", message, new_level)

        levelstat.xp = new_xp
        levelstat.level = new_level
        await levelstat.save()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.channel in message.guild.get_channel(self.CATEGORY_ID).channels:
            await self._update_xp(message, message.author.id, self.AMOUNT)

    @commands.Cog.listener()
    async def on_level_up(self, message, new_level):
        await message.channel.send(
            f"{message.author.mention}, has leveled up to level `{new_level}`! "
            f"{constant.Emoji.aaa}"
        )

    @commands.guild_only()
    @commands.command(aliases=["level"])
    async def rank(self, ctx: commands.Context, member: discord.Member = None):
        """Show a member rank stats."""

        member = member or ctx.author
        levelstat = await models.LevelStat.get_or_none(
            guild_id=ctx.guild.id, member_id=member.id
        )

        if levelstat is None:
            return await ctx.send("Rank not found!")

        levelstat_member_ids = (
            await models.LevelStat.filter(guild_id=ctx.guild.id)
            .order_by("-level")
            .values("member_id")
        )
        position = levelstat_member_ids.index({"member_id": member.id}) + 1

        min_xp = levelstat.level**5
        next_level_xp = (levelstat.level + 1) ** 5
        xp_required = next_level_xp - min_xp
        xp_have = levelstat.xp - min_xp
        percentage = round((xp_have * 100) / xp_required)

        filled_length = int(25 * percentage // 100)
        bar = "▓" * filled_length + "░" * (25 - filled_length)

        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_author(name=member.name, icon_url=member.display_avatar.url)
        embed.description = (
            f"LVL: `{levelstat.level}` XP: `{levelstat.xp:,}`/`{next_level_xp:,}`\n"
            f"Leadboard position: `{position:,}`/`{len(levelstat_member_ids):,}`\n"
            f"```[{bar}] {percentage}%```".replace(",", ".")
        )
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(aliases=["lb"])
    async def leaderboard(self, ctx: commands.Context):
        """Show the guild leaderboard."""

        entries = []
        levelstat = await models.LevelStat.filter(guild_id=ctx.guild.id).order_by(
            "-level"
        )

        for i, ls in enumerate(levelstat):
            member = ctx.guild.get_member(ls.member_id)  # Fuck you fetch_user
            mention = ctx.mention(ls.member_id) if member is None else member.mention
            entries.append(
                f"`{i + 1}` - {mention} LVL: `{ls.level}` XP: `{ls.xp:,}`\n".replace(
                    ",", "."
                )
            )

        menu = menus.MenuPages(
            DescriptionSource(entries, title="Level Leadboard", per_page=15),
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

                await self._update_xp(message, message.author.id, amount=self.AMOUNT)
            await log_message.edit(content=f"Done {channel.mention}")
        await ctx.send("All done!")
