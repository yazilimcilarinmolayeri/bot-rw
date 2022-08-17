import random
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands, menus

from utils import lists, paginator, models, functions


async def setup(bot):
    await bot.add_cog(Info(bot))


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=["a"])
    async def avatar(self, ctx, member: discord.Member = None):
        """Shows a user's avatar."""

        if member is None:
            member = ctx.author

        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_author(name=member)
        embed.set_image(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")

        await ctx.send(embed=embed)

    @commands.command(aliases=["ui"])
    async def userinfo(self, ctx, member: discord.Member = None):
        """Shows info about a user."""

        if member is None:
            member = ctx.author

        badges = []
        perms = member.guild_permissions
        days = lambda date: (datetime.now(timezone.utc) - date).days
        join_position = (
            sorted(ctx.guild.members, key=lambda member: member.joined_at).index(member)
            + 1
        )

        if perms.administrator:
            badges.append(lists.badges["administrator"])
        if perms.manage_messages:
            badges.append(lists.badges["moderator"])
        if days(member.joined_at) >= days(ctx.guild.created_at) - 365:
            badges.append(lists.badges["oldmember"])

        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_author(name=member)
        embed.description = (
            f"Profile: {member.mention} {' '.join(badges)}\n"
            f"Create: {ctx.format_date(member.created_at)}\n"
            f"Join: {ctx.format_date(member.joined_at)}\n"
            f"Server join position: `{join_position}/{len(ctx.guild.members)}`"
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")

        await ctx.send(embed=embed)

    @commands.command(aliases=["si"])
    async def serverinfo(self, ctx, guild_id=None):
        """Shows info about the current server."""

        if guild_id is not None and await self.bot.is_owner(ctx.author):
            guild = self.bot.get_guild(guild_id)

            if guild is None:
                return await ctx.send("Guild not found!")
        else:
            guild = ctx.guild

        description = (
            f"{guild.description}\n\n" if guild.description is not None else " "
        )
        channel_count = len(guild.text_channels) + len(guild.voice_channels)

        if guild.premium_tier > 0:
            last_boosts = (
                ", ".join(
                    "{} ({})".format(m.mention, ctx.format_relative(m.premium_since))
                    for i, m in enumerate(guild.premium_subscribers[:10])
                )
                if len(guild.premium_subscribers)
                else "`?`"
            )
            boosts_info = (
                f"Level: `{guild.premium_tier} "
                f"({guild.premium_subscription_count} boost)`\n"
                f"Last boost(s): {last_boosts}"
            )
        else:
            boosts_info = ""

        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_author(name=guild)
        embed.description = (
            f"{description}"
            f"Total member: `{guild.member_count}`\n"
            f"Role count: `{len(guild.roles)}`\n"
            f"Channel count: `{channel_count}`\n"
            f"Emoji count: `{len(guild.emojis)}`\n"
            f"Owner: {guild.owner.mention}\n"
            f"Created: {ctx.format_date(guild.created_at)}\n\n{boosts_info}"
        )
        embed.set_thumbnail(url=guild.icon.url)
        embed.set_footer(text=f"ID: {guild.id}")

        await ctx.send(embed=embed)

    @commands.command(aliases=["c"])
    async def channel(self, ctx, channel: discord.TextChannel = None):
        """Shows info about the text channel."""

        pass

    @commands.command()
    async def roles(self, ctx):
        """Lists roles in the server."""

        roles = ", ".join([r.mention for r in ctx.guild.roles[1:]])

        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_author(name=ctx.guild)
        embed.description = f"Total: `{len(ctx.guild.roles)}`\n\n{roles}"

        await ctx.send(embed=embed)

    @commands.command(aliases=["e"])
    async def emojis(self, ctx, guild_id=None):
        """Shows you about the emoji info int the server."""

        embeds = []

        if guild_id is not None and await self.bot.is_owner(ctx.author):
            guild = self.bot.get_guild(guild_id)

            if guild is None:
                return await ctx.send("Server not found!")
        else:
            guild = ctx.guild

        for emojis in functions.list_to_matrix(guild.emojis):
            embed = discord.Embed(color=self.bot.embed_color)
            embed.set_author(name=guild)

            emojis = "\n".join(
                [
                    f"{ctx.get_emoji(guild, e.id)} " f"`{ctx.get_emoji(guild, e.id)}`"
                    for e in emojis
                ]
            )

            embed.description = f"Total: `{len(guild.emojis)}`\n\n{emojis}"
            embeds.append(embed)

        menu = menus.MenuPages(
            timeout=30,
            clear_reactions_after=True,
            source=paginator.EmbedSource(data=embeds),
        )
        await menu.start(ctx)

    @commands.command()
    async def fetch(
        self,
        ctx,
        channel: discord.TextChannel = None,
        author: discord.Member = None,
    ):
        """Brings a message from the past (1 year ago)."""

        if channel is None:
            channel = ctx
        else:
            perms = channel.permissions_for(ctx.author)

            if not perms.view_channel:
                return await ctx.send("You are not perm to view this channel!")

        messages = [
            message
            async for message in channel.history(
                before=datetime.today() - timedelta(days=365)
            )
        ]

        if author is not None:
            messages = [m for m in messages if author.id == m.author.id]

        if not len(messages):
            return await ctx.send("Message not found!")

        message = random.choice(messages)
        author = message.author

        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_author(name=author, icon_url=author.display_avatar.url)
        embed.description = (
            f"{message.content}\n\nOriginal: [Jump!]({message.jump_url})\n"
            f"Created: {ctx.format_date(message.created_at)}"
        )

        await ctx.send(embed=embed)

    async def send_profile_message(self, author):
        channel = self.bot.get_channel(
            self.bot.config.getint("channels", "profile_channel_id")
        )
        command = self.bot.get_command("profile")
        await command.__call__(channel, member=author)

    @commands.group(invoke_without_command=True)
    async def profile(self, ctx, member: discord.Member = None):
        """Shows info a user profile."""

        if member is None:
            member = ctx.author

        data = await models.Profile.values_list(pk=member.id)

        if not len(data):
            return await ctx.send("Profile not found!")

        screenshot_url = data[-1]
        data = data[1:-1]

        embed = discord.Embed(color=self.bot.embed_color, timestamp=datetime.utcnow())
        embed.set_author(name=member, icon_url=member.display_avatar.url)
        embed.description = "\n".join(
            [f"{lists.profile_titles[i]}: `{j}`" for i, j in enumerate(data)]
        )
        # embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_image(url=screenshot_url if screenshot_url != "?" else None)

        await ctx.send(embed=embed)

    @profile.command(name="setup")
    async def profile_setup(self, ctx):
        """Setup a user profile."""

        answers = {}
        fields = [
            "user_id",
            "operation_system",
            "desktop_environment",
            "desktop_themes",
            "web_browser",
            "code_editors",
            "terminal_software",
            "shell_software",
            "screenshot_url",
        ]
        author = ctx.message.author
        answers[fields[0]] = author.id

        p = await models.Profile.values_list(pk=author.id)

        if len(p):
            return await ctx.send("You have a profile, please be edit.")

        def check(m):
            try:
                return (m.channel.id == ctx.channel.id) and (m.author.id == author.id)
            except:
                return False

        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_footer(text="'s' for skip question, 'c' for cancel setup")
        question_embed = await ctx.send(embed=embed)

        for i, question in enumerate(lists.profile_questions):
            embed.description = f"{author.mention} {question}"
            await question_embed.edit(embed=embed)
            answer = await self.bot.wait_for("message", check=check)

            if answer.content.lower() == "s":
                answers[fields[i + 1]] = "?"
            elif answer.content.lower() == "c":
                return await question_embed.delete()
            else:
                if len(lists.profile_questions) - 1 == i:
                    if not functions.is_url_image(answer.content):
                        await ctx.send(
                            "Invalid link, skiping question...",
                            delete_after=3.0,
                        )
                        answers[fields[i + 1]] = "?"
                        continue

                answers[fields[i + 1]] = answer.content
            await answer.delete()

        await models.Profile.create(**answers)

        embed.description = f"{author.mention} setup complete!"
        embed.set_footer(text=None)
        await question_embed.edit(embed=embed)

        await self.send_profile_message(author)

    @profile.group(name="remove")
    @commands.has_permissions(manage_messages=True)
    async def profile_remove(self, ctx, member: discord.Member):
        """Remove a user profile."""

        await models.Profile.get(pk=member.id).delete()
        await ctx.send(f"`{member}`s profile has been removed.")

    @profile.group(name="edit")
    async def profile_edit(self, ctx):
        """Edit a user profile."""

        commands = ctx.command.commands
        sub_commands = ", ".join([f"`{c.aliases[0]}`" for c in commands])

        embed = discord.Embed(color=self.bot.embed_color)
        embed.description = f"Sub commands for profile edit:\n{sub_commands}"

        if not ctx.invoked_subcommand:
            await ctx.send(embed=embed)

    @profile_edit.command(aliases=["os"])
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def operation_system(self, ctx, *, new_profile_item):
        await models.Profile.get(pk=ctx.author.id).update(
            operation_system=new_profile_item
        )
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
        await self.send_profile_message(ctx.author)

    @profile_edit.command(aliases=["de"])
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def desktop_environment(self, ctx, *, new_profile_item):
        await models.Profile.get(pk=ctx.author.id).update(
            desktop_environment=new_profile_item
        )
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
        await self.send_profile_message(ctx.author)

    @profile_edit.command(aliases=["themes"])
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def desktop_themes(self, ctx, *, new_profile_item):
        await models.Profile.get(pk=ctx.author.id).update(
            desktop_themes=new_profile_item
        )
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
        await self.send_profile_message(ctx.author)

    @profile_edit.command(aliases=["browser"])
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def web_browser(self, ctx, *, new_profile_item):
        await models.Profile.get(pk=ctx.author.id).update(web_browser=new_profile_item)
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
        await self.send_profile_message(ctx.author)

    @profile_edit.command(aliases=["editors"])
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def code_editors(self, ctx, *, new_profile_item):
        await models.Profile.get(pk=ctx.author.id).update(code_editors=new_profile_item)
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
        await self.send_profile_message(ctx.author)

    @profile_edit.command(aliases=["terminal"])
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def terminal_software(self, ctx, *, new_profile_item):
        await models.Profile.get(pk=ctx.author.id).update(
            terminal_software=new_profile_item
        )
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
        await self.send_profile_message(ctx.author)

    @profile_edit.command(aliases=["shell"])
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def shell_software(self, ctx, *, new_profile_item):
        await models.Profile.get(pk=ctx.author.id).update(
            shell_software=new_profile_item
        )
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
        await self.send_profile_message(ctx.author)

    @profile_edit.command(aliases=["ss"])
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def screenshot_url(self, ctx, new_profile_item):
        if not functions.is_url_image(new_profile_item):
            return await ctx.message.add_reaction("\N{DOUBLE EXCLAMATION MARK}")

        await models.Profile.get(pk=ctx.author.id).update(
            screenshot_url=new_profile_item
        )
        await ctx.message.add_reaction("N{WHITE HEAVY CHECK MARK}")
        await self.send_profile_message(ctx.author)
