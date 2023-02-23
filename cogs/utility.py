import os
import time
import random
import inspect
import platform
from datetime import datetime

import arrow
import psutil
import discord
from discord.ext import commands

from utils import constant


async def setup(bot):
    await bot.add_cog(Utility(bot))


class HelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__(
            command_attrs={
                "aliases": ["h"],
                "help": "Shows help about the bot, a command, or a category.",
            }
        )

        self.owner_cogs = ["Owner"]
        self.ignore_cogs = ["Events", "Jishaku"]

    async def send_bot_help(self, mapping):
        fields = []
        total_command = 0
        ctx = self.context

        for extension in ctx.bot.cogs.values():
            commands = [f"`{c.qualified_name}`" for c in mapping[extension]]
            total_command += len(commands)

            if len(commands) == 0:
                continue
            if extension.qualified_name in self.ignore_cogs:
                continue
            if (
                not (await ctx.bot.is_owner(ctx.author))
                and extension.qualified_name in self.owner_cogs
            ):
                continue

            fields.append(f"{extension.qualified_name}: {', '.join(commands)}")

        embed = discord.Embed(color=ctx.bot.embed_color, title="Help Page")
        embed.description = (
            f"Use `{ctx.prefix}help [command=None]` for more info on a command.\n"
            "`<argument>`: This means the argument is required.\n"
            "`[argument]`: This means the argument is optional.\n"
            "`[A|B]`: This means that it can be either A or B.\n"
            "`[argument...]`: This means you can have multiple arguments.\n\n"
        )
        embed.add_field(name="Commands", value="\n".join(fields))
        embed.set_footer(
            text=(
                f"Total cog: {len(ctx.bot.cogs.values())} - "
                f"Total command: {total_command}"
            )
        )

        await ctx.send(embed=embed)

    def get_command_signature(self, command):
        parent = command.full_parent_name

        if len(command.aliases) > 0:
            aliases = "|".join(command.aliases)
            fmt = f"[{command.name}|{aliases}]"

            if parent:
                fmt = f"{parent} {fmt}"

            alias = fmt
        else:
            alias = command.name if not parent else f"{parent} {command.name}"

        return f"{alias} {command.signature}".strip()

    def common_command_formatting(self, command):
        command_signature = self.get_command_signature(command)

        description = (
            f"Usage: `{command_signature.strip()}`\n"
            f"Help: {command.help or 'No help.'}".strip()
        )

        cooldown = command._buckets._cooldown

        if cooldown:
            description += f"\nCooldown: `{cooldown.rate}` per `{cooldown.per}` second."

        return description

    async def send_command_help(self, command):
        embed = discord.Embed(color=self.context.bot.embed_color)
        embed.description = self.common_command_formatting(command)

        await self.context.send(embed=embed)

    async def send_group_help(self, group):
        group_commands = ""

        if len(group.commands) == 0:
            return await self.send_command_help(group)

        for command in group.commands:
            command_signature = (
                self.get_command_signature(command)
                .replace(command.full_parent_name, "")
                .strip()
            )
            group_commands += f"{command_signature}\n"

        embed = discord.Embed(color=self.context.bot.embed_color)
        embed.description = f"{self.common_command_formatting(group)}\n\n"
        embed.add_field(name="Subcommand", value=f"```{group_commands}```")

        await self.context.send(embed=embed)


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.process = psutil.Process()

        self._original_help_command = bot.help_command
        bot.help_command = HelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command

    @commands.command(aliases=["u"])
    async def uptime(self, ctx: commands.Context):
        """Tells you how long the bot has been up for."""

        delta_uptime = datetime.utcnow() - self.bot.launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        await ctx.send(f"Uptime: `{days}`d `{hours}`h `{minutes}`m `{seconds}`s")

    @commands.command(aliases=["p"])
    async def ping(self, ctx: commands.Context, member: discord.Member = None):
        """Used to test bot's response time."""

        if member is not None:
            return await ctx.send(
                "\n".join(
                    [
                        line.replace("you", member.mention)
                        for line in constant.never_gonna_give_you_up_lyrics
                    ]
                )
            )

        before = time.monotonic()
        message = await ctx.send("Pinging...")
        ping = (time.monotonic() - before) * 1000
        await message.edit(content=f"Pong: `{round(ping, 2)}` ms")

    async def say_permissions(
        self,
        ctx: commands.Context,
        member: discord.Member,
        channel: discord.TextChannel,
    ):
        allowed, denied = [], []
        permissions = channel.permissions_for(member)
        embed = discord.Embed(colour=self.bot.embed_color)
        embed.set_author(name=member)

        for name, value in permissions:
            name = name.replace("_", " ").replace("guild", "server").title()

            if value:
                allowed.append(f"`{name}`")
            else:
                denied.append(f"`{name}`")

        embed.description = "Allowed: {}\n\nDenied: {}".format(
            ", ".join(allowed), ", ".join(denied)
        )
        embed.set_footer(text=f"ID: {member.id}")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def perms(
        self,
        ctx: commands.Context,
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
    async def botperms(
        self, ctx: commands.Context, *, channel: discord.TextChannel = None
    ):
        """Shows the bot's permissions in a specific channel."""

        channel = channel or ctx.channel
        member = ctx.guild.me
        await self.say_permissions(ctx, member, channel)

    @commands.command()
    async def source(self, ctx: commands.Context, *, command: str = None):
        """Displays my full source code or for a specific command."""

        branch = "main"
        source_url = "https://github.com/yazilimcilarinmolayeri/ymybot-rw"

        if command is None:
            return await ctx.send(source_url)

        if command == "help":
            src = type(self.bot.help_command)
            filename = inspect.getsourcefile(src)
        else:
            obj = self.bot.get_command(command.replace(".", " "))

            if obj is None:
                return await ctx.send("Command not found!")

            src = obj.callback.__code__
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
    async def choose(self, ctx: commands.Context, *choices: commands.clean_content):
        """Chooses between multiple choices."""

        if len(choices) < 2:
            return await ctx.send("Not enough choices to pick from.")

        await ctx.send(random.choice(choices))

    async def get_last_commits(self, ctx: commands.Context, per_page=3):
        commits = []
        repo = "yazilimcilarinmolayeri/ymybot-rw"
        url = f"https://api.github.com/repos/{repo}/commits?per_page={per_page}"

        async with self.bot.web_client.get(url) as r:
            data = await r.json()

        for commit in data:
            date = arrow.get(commit["commit"]["committer"]["date"])
            commits.append(
                {
                    "sha": commit["sha"],
                    "html_url": commit["html_url"],
                    "message": commit["commit"]["message"],
                    "date": discord.utils.format_dt(date, style="R"),
                }
            )

        return "\n".join(
            [f"- [{c['message']}]({c['html_url']}) ({c['date']})" for c in commits]
        )

    @commands.command(aliases=["info"])
    async def about(self, ctx: commands.Context):
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
        memory_usage = self.process.memory_full_info().uss / 1024**2
        commits = await self.get_last_commits(ctx)

        embed = discord.Embed(color=self.bot.embed_color, title=self.bot.user.name)
        embed.description = (
            f"{self.bot.description}\n\n"
            f"Total guild(s): `{guilds}`\nTotal channel(s): `{text + voice}`\n"
            f"Text channel: `{text}` Voice channel: `{voice}`\n"
            f"Total member(s): `{total_members}` Unique: `{total_unique}`\n\n"
            "**Server States**\n"
            f"Language: `Python {platform.python_version()}`\n"
            f"Library: `discord.py {discord.__version__}`\n"
            f"CPU usage: `{round(cpu_usage, 1)}%` "
            f"Memory usage: `{round(memory_usage, 1)} MiB`\n"
            f"Platform: `{platform.freedesktop_os_release()['PRETTY_NAME']}`\n\n"
            f"**Last Changes**\n{commits}"
        )
        embed.set_footer(text=f"ID: {self.bot.user.id}")
        await ctx.send(embed=embed)
