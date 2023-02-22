from typing import Union

import discord
from discord.utils import format_dt
from discord.ext import commands, menus

from utils import constant
from utils.paginator import DescriptionSource


async def setup(bot):
    await bot.add_cog(Info(bot))


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=["a"])
    async def avatar(
        self, ctx: commands.Context, *, user: Union[discord.Member, discord.User] = None
    ):
        """Shows a user's avatar."""

        user = user or ctx.author
        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_author(name=user)
        embed.set_image(url=user.display_avatar.url)
        embed.set_footer(text=f"ID: {user.id}")
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(aliases=["ui"])
    async def userinfo(
        self, ctx: commands.Context, *, user: Union[discord.Member, discord.User] = None
    ):
        """Shows info about a user."""

        badges = []
        user = user or ctx.author
        join_position = (
            sorted(ctx.guild.members, key=lambda user: user.joined_at).index(user) + 1
        )

        if user.guild_permissions.administrator:
            badges.append(constant.Badge.administrator)
        if user.guild_permissions.manage_messages:
            badges.append(constant.Badge.moderator)
        if join_position <= round(ctx.guild.member_count / 3):  # TODO: ?
            badges.append(constant.Badge.olduser)

        embed = discord.Embed(color=self.bot.embed_color)
        embed.description = (
            f"{' '.join(badges)}\n\n"
            f"Profile: {user.mention}\n"
            f"Created: {format_dt(user.created_at)}\n"
            f"Joined: {format_dt(user.joined_at)}\n"
            f"Server join position: `{join_position}/{ctx.guild.member_count}`"
        )
        embed.set_author(name=user.name)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"ID: {user.id}")
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(aliases=["si"])
    async def serverinfo(self, ctx: commands.Context, *, guild_id: int = None):
        """Shows info about the current server."""

        if guild_id is not None and await self.bot.is_owner(ctx.author):
            guild = self.bot.get_guild(guild_id)

            if guild is None:
                return await ctx.send("Invalid guild ID given.")
        else:
            guild = ctx.guild

        if guild.premium_tier:
            last_boosts = [
                f"{member.mention} ({format_dt(member.premium_since, style='R')})"
                for member in guild.premium_subscribers
            ]
            boosts_information = (
                f"Level: `{guild.premium_tier}` "
                f"Total boost: `{guild.premium_subscription_count}`\n"
                f"Last boost(s): {', '.join(last_boosts)}"
            )
        else:
            boosts_information = None

        embed = discord.Embed(color=self.bot.embed_color)
        embed.description = (
            f"{guild.description or ''}\n\n"
            f"Owner: {guild.owner.mention}\n"
            f"Created: {format_dt(guild.created_at)}\n"
            f"Channel: `{len(guild.channels)}` "
            f"Role: `{len(guild.roles)}` "
            f"Member: `{guild.member_count}` "
            f"Emoji: `{len(guild.emojis)}`\n\n"
            f"{boosts_information or ''}"
        )
        embed.set_author(name=guild.name)

        if guild.icon is not None:
            embed.set_thumbnail(url=guild.icon.url)

        embed.set_footer(text=f"ID: {guild.id}")
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(aliases=["jl"])
    async def joinlist(self, ctx: commands.Context, *, guild_id: int = None):
        """Displays the server's join list."""

        entries = []

        if guild_id is not None and await self.bot.is_owner(ctx.author):
            guild = self.bot.get_guild(guild_id)

            if guild is None:
                return await ctx.send("Invalid guild ID given.")
        else:
            guild = ctx.guild

        join_list = sorted(guild.members, key=lambda member: member.joined_at)

        for index, member in enumerate(join_list):
            joined_at = format_dt(member.joined_at, style="R")
            entries.append(f"`{index + 1}` - {joined_at} {member.mention}\n")

        menu = menus.MenuPages(
            DescriptionSource(entries, title="Server Join List", per_page=30),
            clear_reactions_after=True,
        )
        await menu.start(ctx)

    @commands.guild_only()
    @commands.command(aliases=["bl"])
    async def banlog(self, ctx: commands.Context):
        """Grabs the 50 most recent bans from the audit log."""

        entries = []

        async for entry in ctx.guild.audit_logs(action=discord.AuditLogAction.ban):
            created_at = format_dt(entry.created_at, style="R")
            entries.append(
                f"Banned: {created_at} `{entry.target}`\n"
                f"Moderator: `{entry.user}`\n"
                f"Reason: `{entry.reason.strip()}`\n\n"
            )

        menu = menus.MenuPages(
            DescriptionSource(entries, title="Ban Log", per_page=5),
            clear_reactions_after=True,
        )
        await menu.start(ctx)

    @commands.guild_only()
    @commands.command()
    async def roles(self, ctx: commands.Context, *, guild_id: int = None):
        """Lists roles in the server."""

        if guild_id is not None and await self.bot.is_owner(ctx.author):
            guild = self.bot.get_guild(guild_id)

            if guild is None:
                return await ctx.send("Invalid guild ID given.")
        else:
            guild = ctx.guild

        role_name_list = [f"{role.mention}" for role in guild.roles]
        # role_name_list.pop(0)  # @everyone
        role_name_list.reverse()
        embed = discord.Embed(color=self.bot.embed_color)
        embed.description = ", ".join(role_name_list)
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(aliases=["e"])
    async def emojis(self, ctx: commands.Context, *, guild_id: int = None):
        """Shows you about the emoji info int the server."""

        if guild_id is not None and await self.bot.is_owner(ctx.author):
            guild = self.bot.get_guild(guild_id)

            if guild is None:
                return await ctx.send("Invalid guild ID given.")
        else:
            guild = ctx.guild

        if not len(guild.emojis):
            return await ctx.send("Custom emoji not found.")

        entries = [f"{emoji} - `{emoji}`\n" for emoji in guild.emojis]
        menu = menus.MenuPages(
            DescriptionSource(entries, title="Emoji List", per_page=10),
            clear_reactions_after=True,
        )
        await menu.start(ctx)
