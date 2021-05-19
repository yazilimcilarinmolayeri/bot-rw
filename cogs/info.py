# -*- coding: utf-8 -*-

import os
import random
import discord
import inspect
import mimetypes
from utils import config, lists
from discord.ext import commands
from datetime import datetime, timedelta, timezone


def setup(bot):
    bot.add_cog(Info(bot))


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    def is_url_image(self, url):
        mimetype, encoding = mimetypes.guess_type(url)
        return mimetype and mimetype.startswith("image")

    async def send_profile_message(self, author):
        channel = self.bot.get_channel(config.PROFILE_CHANNEL_ID)
        command = self.bot.get_command("profile")

        await command.__call__(ctx=channel, user=author)

    @commands.command(aliases=["ui"])
    async def userinfo(self, ctx, member: discord.Member = None):
        """"""

        badges = []

        if member == None:
            member = ctx.author

        created_at = member.created_at
        joined_at = member.joined_at
        c_day, c_month, c_year = (
            created_at.day,
            created_at.month,
            created_at.year,
        )
        j_day, j_month, j_year = (
            joined_at.day,
            joined_at.month,
            joined_at.year,
        )
        j_days = (datetime.now(timezone.utc) - joined_at).days
        c_days = (datetime.now(timezone.utc) - created_at).days

        perms = member.guild_permissions
        partner_role = ctx.guild.get_role(config.PARTNER_ROLE_ID)
        sponsor_role = ctx.guild.get_role(config.SPONSOR_ROLE_ID)

        is_role = lambda role: True if role in member.roles else False

        if perms.administrator:
            badges.append("<:administrator:844298864869769226>")
        if perms.manage_messages:
            badges.append("<:moderator:844298864857055252>")
        if j_days > 365 * 2:
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
                "{}.{}.{} ({} gün önce)".format(
                    j_day,
                    j_month,
                    j_year,
                    j_days,
                ),
                "{}.{}.{} ({} gün önce)".format(
                    c_day,
                    c_month,
                    c_year,
                    c_days,
                ),
            )
        )
        embed.set_thumbnail(url=member.avatar.url)
        embed.set_footer(text="ID: {}".format(member.id))

        await ctx.send(embed=embed)

    @commands.command(aliases=["gi"])
    async def guildinfo(self, ctx, guild: discord.Guild = None):
        """"""

        if guild == None:
            guild = ctx.guild

        created_at = guild.created_at
        c_day, c_month, c_year = (
            created_at.day,
            created_at.month,
            created_at.year,
        )
        c_days = (datetime.now(timezone.utc) - created_at).days
        subs = guild.premium_subscribers

        embed = discord.Embed(color=self.bot.color)
        embed.set_author(name=guild)
        embed.description = (
            "{}"
            "Üye sayısı: `{}` "
            "Rol sayısı: `{}`\n"
            "Kanal sayısı: `{}` "
            "Emoji sayısı: `{}`\n"
            "Sahip: {}\n"
            "Oluşturulma tarihi: `{}`\n\n"
            "Seviye: `{}`\n"
            "Toplam takviye: `{}`\n"
            "Son takviye(ler): {}".format(
                "{}\n\n".format(guild.description)
                if guild.description != None
                else " ",
                guild.member_count,
                len(guild.roles),
                len(guild.text_channels) + len(guild.voice_channels),
                len(guild.emojis),
                guild.owner.mention,
                "{}.{}.{} ({} gün önce)".format(
                    c_day,
                    c_month,
                    c_year,
                    c_days,
                ),
                guild.premium_tier,
                guild.premium_subscription_count,
                ", ".join(m.mention for m in subs) if len(subs) else "`Yok`",
            )
        )
        embed.set_thumbnail(url=guild.icon.url)
        embed.set_footer(text="ID: {}".format(guild.id))

        await ctx.send(embed=embed)

    @commands.command(aliases=["getir"])
    async def get(
        self,
        ctx,
        channel: discord.TextChannel = None,
        author: discord.Member = None,
    ):
        """"""

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
        day, month, year = (
            message.created_at.day,
            message.created_at.month,
            message.created_at.year,
        )

        embed = discord.Embed(color=self.bot.color)
        embed.set_author(name=author, icon_url=author.avatar.url)
        embed.description = "{}\n\n[`Mesaja zıpla!`]({})".format(
            message.content, message.jump_url
        )
        embed.set_footer(
            text="{}.{}.{} {}".format(
                day, month, year, "- Bot" if author.bot else " "
            )
        )

        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True)
    async def profile(self, ctx, user: discord.Member = None):
        """"""

        if user is None:
            user = ctx.author

        data = self.db.get_item("Profile", ("user_id", user.id))

        if not len(data):
            return await ctx.send("Profil bulunamadı!")

        data = data[0]

        embed = discord.Embed(
            color=self.bot.color, timestamp=datetime.utcnow()
        )
        embed.description = "{} **{}**\n\n".format(
            user.mention, user
        ) + "\n".join(
            [
                "{}: `{}`".format(lists.profile_titles[i], j)
                for i, j in enumerate(data[1:-1])
            ]
        )
        embed.set_thumbnail(url=user.avatar.url)
        embed.set_image(
            url=data[-1] if data[-1] != "-" else discord.Embed.Empty
        )
        embed.set_footer(text="ID: {}".format(user.id))

        await ctx.send(embed=embed)

    @profile.command(name="setup")
    async def profile_setup(self, ctx):
        """"""

        answers = []
        author = ctx.message.author
        answers.append(author.id)

        if self.db.check_item("Profile", ("user_id", author.id)):
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
            text="'S' girerek soruyu geçebilir, 'C' girerek iptal edebilirsin."
        )
        question_embed = await ctx.send(embed=embed)

        for i, question in enumerate(lists.profile_questions):
            embed.description = "{}, {}".format(author.mention, question)
            await question_embed.edit(embed=embed)
            answer = await self.bot.wait_for("message", check=check)

            if answer.content.lower() == "s":
                answers.append("-")
            elif answer.content.lower() == "c":
                return await question_embed.delete()
            else:
                if len(lists.profile_questions) - 1 == i:
                    if not self.is_url_image(answer.content):
                        return await ctx.send(
                            "Geçersiz bağlantı! Çıkılıyor..."
                        )
                answers.append(answer.content)

            await answer.delete()

        self.db.insert("Profile", *answers)

        profile_channel = self.bot.get_channel(config.PROFILE_CHANNEL_ID)
        embed.description = "{}, Kurulum tamamlandı! Gözat: {}".format(
            author.mention, profile_channel.mention
        )
        embed.set_footer(text=discord.Embed.Empty)

        await question_embed.edit(embed=embed)
        await self.send_profile_message(ctx.message.author)

    @profile.group(name="delete")
    @commands.has_permissions(manage_messages=True)
    async def profile_delete(self, ctx, user: discord.Member):
        """"""

        if not self.db.check_item("Profile", ("user_id", user.id)):
            return await ctx.send("Profil bulunamadı!")

        self.db.remove("Profile", ("user_id", user.id))
        await ctx.send(
            "{} adlı kullanıcının profili silindi!".format(user.mention)
        )

    @profile.group(name="edit")
    async def profile_edit(self, ctx):
        """"""

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
        self.db.update(
            "Profile",
            ("user_id", ctx.message.author.id),
            operation_system=new_profile_item,
        )

        await ctx.message.add_reaction("\U00002705")
        await self.send_profile_message(ctx.message.author)

    @profile_edit.command(aliases=["de"])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def desktop_environment(self, ctx, *, new_profile_item):
        self.db.update(
            "Profile",
            ("user_id", ctx.message.author.id),
            desktop_environment=new_profile_item,
        )

        await ctx.message.add_reaction("\U00002705")
        await self.send_profile_message(ctx.message.author)

    @profile_edit.command(aliases=["themes"])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def desktop_themes(self, ctx, *, new_profile_item):
        self.db.update(
            "Profile",
            ("user_id", ctx.message.author.id),
            desktop_themes=new_profile_item,
        )

        await ctx.message.add_reaction("\U00002705")
        await self.send_profile_message(ctx.message.author)

    @profile_edit.command(aliases=["browser"])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def web_browser(self, ctx, *, new_profile_item):
        self.db.update(
            "Profile",
            ("user_id", ctx.message.author.id),
            web_browser=new_profile_item,
        )

        await ctx.message.add_reaction("\U00002705")
        await self.send_profile_message(ctx.message.author)

    @profile_edit.command(aliases=["editors"])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def code_editors(self, ctx, *, new_profile_item):
        self.db.update(
            "Profile",
            ("user_id", ctx.message.author.id),
            code_editors=new_profile_item,
        )

        await ctx.message.add_reaction("\U00002705")
        await self.send_profile_message(ctx.message.author)

    @profile_edit.command(aliases=["terminal"])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def terminal_software(self, ctx, *, new_profile_item):
        self.db.update(
            "Profile",
            ("user_id", ctx.message.author.id),
            terminal_software=new_profile_item,
        )

        await ctx.message.add_reaction("\U00002705")
        await self.send_profile_message(ctx.message.author)

    @profile_edit.command(aliases=["shell"])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def shell_software(self, ctx, *, new_profile_item):
        self.db.update(
            "Profile",
            ("user_id", ctx.message.author.id),
            shell_software=new_profile_item,
        )

        await ctx.message.add_reaction("\U00002705")
        await self.send_profile_message(ctx.message.author)

    @profile_edit.command(aliases=["ss"])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def screenshot_url(self, ctx, new_profile_item):
        if not self.is_url_image(new_profile_item):
            return await ctx.message.add_reaction("\U0000203c")

        self.db.update(
            "Profile",
            ("user_id", ctx.message.author.id),
            screenshot_url=new_profile_item,
        )

        await ctx.message.add_reaction("\U00002705")
        await self.send_profile_message(ctx.message.author)

    @commands.command(aliases=["kaynak"])
    async def source(self, ctx, *, command=None):
        """"""

        branch = "main"
        source_url = "https://github.com/yazilimcilarinmolayeri/rtfm-bot"

        if command is None:
            return await ctx.send(source_url)

        if command == "help":
            src = type(self.bot.help_command)
            module = src.__module__
            filename = inspect.getsourcefile(src)
        else:
            obj = self.bot.get_command(command.replace(".", " "))

            if obj is None:
                return await ctx.send("Komut bulunamadı!")

            src = obj.callback.__code__
            module = obj.callback.__module__
            filename = src.co_filename

        lines, firstlineno = inspect.getsourcelines(src)
        location = os.path.relpath(filename).replace("\\", "/")
        final_url = "<{}/blob/{}/{}#L{}-L{}>".format(
            source_url,
            branch,
            location,
            firstlineno,
            firstlineno + len(lines) - 1,
        )

        await ctx.send(final_url)
