# -*- coding: utf-8 -*-

import random
import discord
import mimetypes
from discord.ext import commands, menus
from datetime import datetime, timedelta, timezone
from utils import lists, paginator, models, time as util_time


def setup(bot):
    bot.add_cog(Info(bot))


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.c = bot.config

    @commands.group(invoke_without_command=True, aliases=["a"])
    async def avatar(self, ctx, member: discord.Member = None):
        """Shows a user's avatar."""

        if member == None:
            member = ctx.author

        formats = ["png", "jpg", "webp"]
        url = lambda format: member.avatar.with_static_format(format)

        if member.avatar.is_animated():
            formats.append("gif")

        embed = discord.Embed(color=self.bot.color)
        embed.set_author(name=member)
        embed.description = "Formatlar: {}".format(
            ", ".join(["[`{}`]({})".format(f, url(f)) for f in formats])
        )

        embed.set_image(url=member.avatar.url)
        embed.set_footer(text="ID: {}".format(member.id))

        await ctx.send(embed=embed)

    @avatar.command(name="history", aliases=["h"])
    async def avatar_history(self, ctx, member: discord.Member = None):
        """Shows a user's avatar history."""

        pass

    @commands.command(aliases=["ui"])
    async def userinfo(self, ctx, member: discord.Member = None):
        """Shows info about a user."""

        badges = []

        if member == None:
            member = ctx.author

        created_at = member.created_at
        joined_at = member.joined_at
        j_days = util_time.humanize(joined_at, g=["day"])

        perms = member.guild_permissions
        partner_role = ctx.guild.get_role(
            self.c.get("Role", "PARTNER_ROLE_ID")
        )
        sponsor_role = ctx.guild.get_role(
            self.c.get("Role", "SPONSOR_ROLE_ID")
        )

        is_role = lambda role: True if role in member.roles else False

        if perms.administrator:
            badges.append("<:administrator:844298864869769226>")
        if perms.manage_messages:
            badges.append("<:moderator:844298864857055252>")
        if (datetime.now(timezone.utc) - joined_at).days > 365 * 2:
            badges.append("<:oldmember:844377103000010752>")
        if (
            is_role(partner_role)
            or is_role(sponsor_role)
            or member in ctx.guild.premium_subscribers
        ):
            badges.append("<:supporter:844298864625319946>")

        embed = discord.Embed(color=self.bot.color)
        embed.set_author(name=member)
        embed.description = (
            "{}\n\n"
            "Profil: {}\n"
            "Giriş tarihi: `{}`\n"
            "Oluşturma tarihi: `{}`".format(
                " ".join(badges),
                member.mention,
                "{}/{}/{} ({})".format(
                    *util_time.day_month_year(joined_at),
                    j_days,
                ),
                "{}/{}/{} ({})".format(
                    *util_time.day_month_year(created_at),
                    util_time.humanize(created_at, g=["day"]),
                ),
            )
        )
        embed.set_thumbnail(url=member.avatar.url)
        embed.set_footer(text="ID: {}".format(member.id))

        await ctx.send(embed=embed)

    @commands.command(aliases=["si"])
    async def serverinfo(self, ctx, guild_id=None):
        """Shows info about the current server."""

        if guild_id is not None and await self.bot.is_owner(ctx.author):
            guild = self.bot.get_guild(guild_id)

            if guild is None:
                return await ctx.send("Sunucu bulunamadı!")
        else:
            guild = ctx.guild

        subs = guild.premium_subscribers

        embed = discord.Embed(color=self.bot.color)
        embed.set_author(name=guild)
        embed.description = (
            "{}"
            "Üye sayısı: `{}` "
            "Rol sayısı: `{}`\n"
            "Kanal sayısı: `{}` "
            "Emoji sayısı: `{}`\n"
            "Oluşturulma tarihi: `{}`\n\n"
            "Seviye: `{}`\n"
            "Toplam takviye: `{}`\n\n"
            "Son takviyeci(ler):\n{}".format(
                "{}\n\n".format(guild.description)
                if guild.description != None
                else " ",
                guild.member_count,
                len(guild.roles),
                len(guild.text_channels) + len(guild.voice_channels),
                len(guild.emojis),
                "{}/{}/{} ({})".format(
                    *util_time.day_month_year(guild.created_at),
                    util_time.humanize(guild.created_at, g=["day"]),
                ),
                guild.premium_tier,
                guild.premium_subscription_count,
                "\n".join(
                    "{}. {} `({})`".format(
                        i + 1,
                        m.mention,
                        util_time.humanize(m.premium_since),
                    )
                    for i, m in enumerate(subs)
                )
                if len(subs)
                else "",
            )
        )
        embed.set_thumbnail(url=guild.icon.url)
        embed.set_footer(
            text="Sahip: {} • ID: {}".format(guild.owner, guild.id)
        )

        await ctx.send(embed=embed)

    def list_to_matrix(self, l, col=10):
        return [l[i : i + col] for i in range(0, len(l), col)]

    @commands.command(aliases=["c"])
    async def channel(self, ctx, channel: discord.TextChannel = None):
        """Shows info about the text channel."""

        if channel == None:
            channel = ctx.channel
            messages = await channel.history(limit=2).flatten()
            last_message = messages[-1]
        else:
            last_message = channel.last_message

        embed = discord.Embed(color=self.bot.color)
        embed.set_author(name=ctx.guild)
        embed.description = (
            "Kanal: {}\n"
            "Kategori: `{}`\n"
            "Oluşturma tarihi: `{}`\n\n"
            "Sabitli mesaj: `{}`\n"
            "Son mesaj: {} `({})`".format(
                channel.mention,
                channel.category,
                "{}/{}/{} ({})".format(
                    *util_time.day_month_year(channel.created_at),
                    util_time.humanize(channel.created_at, g=["day"]),
                ),
                len(await channel.pins()),
                last_message.author.mention,
                util_time.humanize(last_message.created_at),
            )
        )
        embed.set_footer(text="ID: {}".format(ctx.channel.id))

        await ctx.send(embed=embed)

    @commands.command()
    async def roles(self, ctx):
        """Lists roles in the server."""

        embed = discord.Embed(color=self.bot.color)
        embed.set_author(name=ctx.guild)
        embed.description = "{}\n\nToplam: `{}`".format(
            ", ".join([r.mention for r in ctx.guild.roles[1:]]),
            len(ctx.guild.roles),
        )
        embed.set_footer(text="ID: {}".format(ctx.guild.id))

        await ctx.send(embed=embed)

    @commands.command(aliases=["e"])
    async def emojis(self, ctx, guild_id=None):
        """Shows you about the emoji info int the server."""

        embeds = []

        if guild_id is not None and await self.bot.is_owner(ctx.author):
            guild = self.bot.get_guild(guild_id)

            if guild is None:
                return await ctx.send("Sunucu bulunamadı!")
        else:
            guild = ctx.guild

        for emojis in self.list_to_matrix(guild.emojis):
            embed = discord.Embed(color=self.bot.color)
            embed.set_author(name=guild)

            embed.description = "\n".join(
                [
                    "{} `{} (Eklendi: {})`".format(
                        ctx.get_emoji(guild, e.id),
                        ctx.get_emoji(guild, e.id),
                        util_time.humanize(e.created_at, g=["day"]),
                    )
                    for e in emojis
                ]
            ) + "\n\nToplam: `{}`\nID: `{}`".format(
                len(guild.emojis), guild.id
            )
            embeds.append(embed)

        menu = menus.MenuPages(
            timeout=30,
            clear_reactions_after=True,
            source=paginator.EmbedSource(data=embeds),
        )
        await menu.start(ctx)

    @commands.command(aliases=["getir"])
    async def get(
        self,
        ctx,
        channel: discord.TextChannel = None,
        author: discord.Member = None,
    ):
        """Brings a message from the past (1 year ago)."""

        if channel == None:
            channel = ctx
        else:
            perms = channel.permissions_for(ctx.author)

            if not perms.view_channel:
                return await ctx.send(
                    "Bu kanalı görme yetkisine sahip değilsin!"
                )

        messages = await channel.history(
            around=datetime.today() - timedelta(days=365)
        ).flatten()

        if author != None:
            messages = [m for m in messages if author.id == m.author.id]

        if not len(messages):
            return await ctx.send("Mesaj bulunamadı!")

        message = random.choice(messages)
        author = message.author

        embed = discord.Embed(color=self.bot.color)
        embed.set_author(name=author, icon_url=author.avatar.url)
        embed.description = "{}\n\n[`Mesaja zıpla!`]({})".format(
            message.content, message.jump_url
        )
        embed.set_footer(
            text="{}/{}/{} {}".format(
                *util_time.day_month_year(message.created_at),
                "• Bot" if author.bot else " ",
            )
        )

        await ctx.send(embed=embed)

    def is_url_image(self, url):
        mimetype, encoding = mimetypes.guess_type(url)
        return mimetype and mimetype.startswith("image")

    async def send_profile_message(self, author):
        channel = self.bot.get_channel(
            self.c.getint("Channel", "PROFILE_CHANNEL_ID")
        )
        command = self.bot.get_command("profile")

        await command.__call__(ctx=channel, member=author)

    @commands.group(invoke_without_command=True)
    async def profile(self, ctx, member: discord.Member = None):
        """Shows info a user profile."""

        if member is None:
            member = ctx.author

        data = await models.Profile.values_list(pk=member.id)

        if not len(data):
            return await ctx.send("Profil bulunamadı!")

        member_id, screenshot_url = data[1], data[-1]
        data = data[1:-1]

        embed = discord.Embed(
            color=self.bot.color, timestamp=datetime.utcnow()
        )
        embed.description = "{} **{}**\n\n".format(
            member.mention, member
        ) + "\n".join(
            [
                "{}: `{}`".format(lists.profile_titles[i], j)
                for i, j in enumerate(data)
            ]
        )
        embed.set_thumbnail(url=member.avatar.url)
        embed.set_image(
            url=screenshot_url
            if screenshot_url != "?"
            else discord.Embed.Empty
        )
        embed.set_footer(text="ID: {}".format(member.id))
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
            return await ctx.send("Var olan profilini düzenle...")

        def check(m):
            try:
                return (m.channel.id == ctx.channel.id) and (
                    m.author.id == author.id
                )
            except:
                return False

        embed = discord.Embed(color=self.bot.color)
        embed.set_footer(
            text="'s' girerek geçebilir, 'c' girerek iptal edebilirsin."
        )
        question_embed = await ctx.send(embed=embed)

        for i, question in enumerate(lists.profile_questions):
            embed.description = "{}, {}".format(author.mention, question)
            await question_embed.edit(embed=embed)
            answer = await self.bot.wait_for("message", check=check)

            if answer.content.lower() == "s":
                answers[fields[i + 1]] = "?"
            elif answer.content.lower() == "c":
                return await question_embed.delete()
            else:
                if len(lists.profile_questions) - 1 == i:
                    if not self.is_url_image(answer.content):
                        await ctx.send("Geçersiz bağlantı! Soru geçiliyor...")
                        answers[fields[i + 1]] = "?"
                answers[fields[i + 1]] = answer.content
            await answer.delete()
        await models.Profile.create(**answers)

        profile_channel = self.bot.get_channel(
            self.c.get("Channel", "PROFILE_CHANNEL_ID")
        )
        embed.description = "{}, Kurulum tamamlandı!".format(author.mention)
        embed.set_footer(text=discord.Embed.Empty)

        await question_embed.edit(embed=embed)
        await self.send_profile_message(ctx.message.author)

    @profile.group(name="remove")
    @commands.has_permissions(manage_messages=True)
    async def profile_remove(self, ctx, member: discord.Member):
        """Remove a user profile."""

        await models.Profile.get(pk=member.id).delete()
        await ctx.send(
            "{} adlı kullanıcının profili silindi!".format(member.mention)
        )

    @profile.group(name="edit")
    async def profile_edit(self, ctx):
        """Edit a user profile."""

        commands = ctx.command.commands

        embed = discord.Embed(color=self.bot.color)
        embed.description = "Profil düzenlemek için argümanlar:\n" + ", ".join(
            "`{}`".format(c.aliases[0]) for c in commands
        )

        if not ctx.invoked_subcommand:
            await ctx.send(embed=embed)

    @profile_edit.command(aliases=["os"])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def operation_system(self, ctx, *, new_profile_item):
        await models.Profile.get(pk=ctx.author.id).update(
            operation_system=new_profile_item
        )
        await ctx.message.add_reaction("\U00002705")
        await self.send_profile_message(ctx.author)

    @profile_edit.command(aliases=["de"])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def desktop_environment(self, ctx, *, new_profile_item):
        await models.Profile.get(pk=ctx.author.id).update(
            desktop_environment=new_profile_item
        )
        await ctx.message.add_reaction("\U00002705")
        await self.send_profile_message(ctx.author)

    @profile_edit.command(aliases=["themes"])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def desktop_themes(self, ctx, *, new_profile_item):
        await models.Profile.get(pk=ctx.author.id).update(
            desktop_themes=new_profile_item
        )
        await ctx.message.add_reaction("\U00002705")
        await self.send_profile_message(ctx.author)

    @profile_edit.command(aliases=["browser"])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def web_browser(self, ctx, *, new_profile_item):
        await models.Profile.get(pk=ctx.author.id).update(
            web_browser=new_profile_item
        )
        await ctx.message.add_reaction("\U00002705")
        await self.send_profile_message(ctx.author)

    @profile_edit.command(aliases=["editors"])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def code_editors(self, ctx, *, new_profile_item):
        await models.Profile.get(pk=ctx.author.id).update(
            code_editors=new_profile_item
        )
        await ctx.message.add_reaction("\U00002705")
        await self.send_profile_message(ctx.author)

    @profile_edit.command(aliases=["terminal"])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def terminal_software(self, ctx, *, new_profile_item):
        await models.Profile.get(pk=ctx.author.id).update(
            terminal_software=new_profile_item
        )
        await ctx.message.add_reaction("\U00002705")
        await self.send_profile_message(ctx.author)

    @profile_edit.command(aliases=["shell"])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def shell_software(self, ctx, *, new_profile_item):
        await models.Profile.get(pk=ctx.author.id).update(
            shell_software=new_profile_item
        )
        await ctx.message.add_reaction("\U00002705")
        await self.send_profile_message(ctx.author)

    @profile_edit.command(aliases=["ss"])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def screenshot_url(self, ctx, new_profile_item):
        if not self.is_url_image(new_profile_item):
            return await ctx.message.add_reaction("\U0000203c")

        await models.Profile.get(pk=ctx.author.id).update(
            screenshot_url=new_profile_item
        )
        await ctx.message.add_reaction("\U00002705")
        await self.send_profile_message(ctx.author)
