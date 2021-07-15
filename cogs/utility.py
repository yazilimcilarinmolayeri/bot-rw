# -*- coding: utf-8 -*-

import os
import time
import arrow
import psutil
import random
import inspect
import discord
import platform
from discord.ext import commands
from utils import lists, functions, time as util_time


def setup(bot):
    bot.add_cog(Utility(bot))


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.c = bot.config
        self.process = psutil.Process()

    @commands.command(aliases=["u"])
    async def uptime(self, ctx):
        """Tells you how long the bot has been up for."""

        await ctx.send(
            "Uptime: `{}`".format(util_time.humanize(self.bot.uptime))
        )

    @commands.command(aliases=["p"])
    async def ping(self, ctx, member: discord.Member = None):
        """Used to test bot's response time."""

        if member != None:
            return await ctx.send(
                "\n".join(
                    [
                        line.replace("you", member.mention)
                        for line in lists.never_gonna_give_you_up_lyrics
                    ]
                )
            )

        before = time.monotonic()
        message = await ctx.send("Pinging...")
        ping = (time.monotonic() - before) * 1000

        await message.edit(content="Pong: `{} ms`".format(round(ping, 2)))

    @commands.command()
    async def tias(self, ctx, channel: discord.TextChannel = None):
        """Send the "try it and see" message."""

        if channel == None:
            channel = ctx

        await channel.send("https://tryitands.ee")

    @commands.command(aliases=["ddg"])
    @commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
    async def lmddgtfy(self, ctx, *, keywords: str):
        """Let me DuckDuckGo that for you."""

        await ctx.send(
            "https://lmddgtfy.net/?q={}".format(keywords.replace(" ", "+"))
        )

    @commands.command()
    @commands.cooldown(rate=1, per=60.0, type=commands.BucketType.user)
    async def feedback(self, ctx, *, content):
        """Gives feedback about the bot."""

        author = ctx.author
        channel = self.bot.get_channel(
            self.c.getint("Channel", "FEEDBACK_CHANNEL_ID")
        )

        if channel is None:
            return

        embed = discord.Embed(
            color=self.bot.color, timestamp=ctx.message.created_at
        )
        embed.set_author(name=author, icon_url=author.avatar.url)
        embed.description = content

        if ctx.guild is not None:
            embed.add_field(
                name="Geri Bildirim Bilgisi",
                value="Kanal: {} `(ID: {})`\n"
                "Sunucu: `{} (ID: {})`".format(
                    ctx.channel.mention,
                    ctx.channel.id,
                    ctx.guild,
                    ctx.guild.id,
                ),
            )

        embed.set_footer(text="ID: {}".format(author.id))

        await channel.send(embed=embed)
        await ctx.send("Geri bildirim gönderildi. Teşekkürler!")

    async def say_permissions(self, ctx, member, channel):
        allowed, denied = [], []
        permissions = channel.permissions_for(member)

        embed = discord.Embed(colour=self.bot.color)
        embed.set_author(name=member, icon_url=member.avatar.url)

        for name, value in permissions:
            name = name.replace("_", " ").replace("guild", "server").title()

            if value:
                allowed.append("`{}`".format(name))
            else:
                denied.append("`{}`".format(name))

        embed.description = "Allowed: {}\n\nDenied: {}".format(
            ", ".join(allowed), ", ".join(denied)
        )
        embed.set_footer(text="ID: {}".format(member.id))

        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def perms(
        self,
        ctx,
        member: discord.Member = None,
        channel: discord.TextChannel = None,
    ):
        """Shows a member's permissions in a specific channel."""

        channel = channel or ctx.channel

        if member is None:
            member = ctx.author

        await self.say_permissions(ctx, member, channel)

    @commands.command()
    @commands.guild_only()
    async def botperms(self, ctx, *, channel: discord.TextChannel = None):
        """Shows the bot's permissions in a specific channel."""

        channel = channel or ctx.channel
        member = ctx.guild.me

        await self.say_permissions(ctx, member, channel)

    @commands.command(aliases=["kaynak"])
    async def source(self, ctx, *, command=None):
        """Displays my full source code or for a specific command."""

        branch = "main"
        source_url = "https://github.com/yazilimcilarinmolayeri/ymybot-rw"

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

    @commands.command()
    async def choose(self, ctx, *choices: commands.clean_content):
        """Chooses between multiple choices."""

        if len(choices) < 2:
            return await ctx.send("En az iki seçenek girmelisin!")

        await ctx.send(random.choice(choices))

    async def get_last_commits(self, per_page=3):
        commits = []
        repo = "yazilimcilarinmolayeri/ymybot-rw"
        url = "https://api.github.com/repos/{}/commits?per_page={}".format(
            repo, per_page
        )

        async with self.bot.session.get(url) as resp:
            if resp.status != 200:
                return await ctx.send("Bağlantı hatası!")
            data = await resp.json()

        for commit in data:
            date = arrow.get(commit["commit"]["committer"]["date"])
            commits.append(
                {
                    "sha": commit["sha"],
                    "html_url": commit["html_url"],
                    "message": commit["commit"]["message"],
                    "date": util_time.humanize(date),
                }
            )

        return commits

    @commands.command(aliases=["info"])
    async def about(self, ctx):
        """Tells you information about the bot itself."""

        guilds = 0
        text, voice = 0, 0
        total_members = 0
        total_unique = len(self.bot.users)

        for guild in self.bot.guilds:
            guilds += 1

            if guild.unavailable:
                continue

            total_members += guild.member_count

            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    text += 1
                elif isinstance(channel, discord.VoiceChannel):
                    voice += 1

        cpu_usage = psutil.cpu_percent() / psutil.cpu_count()
        memory_usage = self.process.memory_full_info().uss / 1024 ** 2
        commits = await self.get_last_commits()

        embed = discord.Embed(color=self.bot.color)
        embed.set_author(name=self.bot.user, icon_url=self.bot.user.avatar.url)
        embed.description = (
            "{}\n\n"
            "Total guild(s): `{}` Channel: `{}`\n"
            "Text channel: `{}` Voice channel: `{}`\n"
            "Total member(s): `{}` Unique: `{}`\n\n"
            "Usage: CPU: `{} %` Memory: `{} MiB`\n"
            "Lang: `python {}` Lib: `discord.py {}`\nPlatform: `{}`\n\n"
            "Last changes:\n{}".format(
                self.bot.description,
                guilds,
                text + voice,
                text,
                voice,
                total_members,
                total_unique,
                round(cpu_usage, 1),
                round(memory_usage, 1),
                platform.python_version(),
                discord.__version__,
                functions.dist()["PRETTY_NAME"],
                "\n".join(
                    [
                        "[`{}`]({}) {} `({})`".format(
                            c["sha"][:6],
                            c["html_url"],
                            c["message"],
                            c["date"],
                        )
                        for c in commits
                    ]
                ),
            )
        )
        embed.set_footer(text="ID: {}".format(self.bot.user.id))

        await ctx.send(embed=embed)
