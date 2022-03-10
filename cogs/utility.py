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

from utils import lists, functions, time as util_time


def setup(bot):
    bot.add_cog(Utility(bot))


class HelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__(
            command_attrs={
                "help": "Shows help about the bot, a command, or a category."
            }
        )

        self.owner_cogs = ["Owner"]
        self.ignore_cogs = ["Events", "Jishaku"]

    async def send_bot_help(self, mapping):
        total = 0
        fields = []
        ctx = self.context
        owners = ctx.bot.owners

        for extension in ctx.bot.cogs.values():
            commands = ["`{}`".format(c.qualified_name) for c in mapping[extension]]
            total += len(commands)

            if len(commands) == 0:
                continue
            if extension.qualified_name in self.ignore_cogs:
                continue
            if (
                not (ctx.author in owners)
                and extension.qualified_name in self.owner_cogs
            ):
                continue

            fields.append(
                "{}: {}".format(extension.qualified_name, ", ".join(commands))
            )

        embed = discord.Embed(color=ctx.bot.color)
        embed.set_author(name="Help Page")
        embed.description = (
            "Hello! Welcome to the help page.\n"
            "Use `{}{}` for more info on a command.\n\n"
            "`<argument>`: This means the argument is required.\n"
            "`[argument]`: This means the argument is optional.\n"
            "`[A|B]`: This means that it can be either A or B.\n"
            "`[argument...]`: This means you can have multiple arguments.\n\n"
            "Commands:\n{}".format(
                ctx.prefix,
                self.get_command_signature(ctx.bot.get_command("help")),
                "\n".join(fields),
            )
        )
        embed.set_footer(
            text="Total cog: {} • Total command: {}".format(
                len(ctx.bot.cogs.values()), total
            )
        )

        await ctx.send(embed=embed)

    def get_command_signature(self, command):
        parent = command.full_parent_name

        if len(command.aliases) > 0:
            aliases = "|".join(command.aliases)
            fmt = "[{}|{}]".format(command.name, aliases)

            if parent:
                fmt = "{} {}".format(parent, fmt)

            alias = fmt
        else:
            alias = command.name if not parent else "{} {}".format(parent, command.name)

        return "{} {}".format(alias, command.signature).strip()

    def common_command_formatting(self, command):
        command_signature = self.get_command_signature(command)

        description = "Usage: `{}`\nHelp: `{}`".format(
            command_signature.strip(),
            (command.help or "Help not found.").strip(),
        )

        cooldown = command._buckets._cooldown

        if cooldown:
            description += "\nCooldown: `{} per {} second`".format(
                cooldown.rate, cooldown.per
            )

        return description

    async def send_command_help(self, command):
        embed = discord.Embed(color=self.context.bot.color)
        embed.description = self.common_command_formatting(command)
        embed.set_footer(text="Cog: {}".format(command.cog_name))

        await self.context.send(embed=embed)

    async def send_group_help(self, group):
        fields = []

        if len(group.commands) == 0:
            return await self.send_command_help(group)

        for command in group.commands:
            fields.append(
                "`{}`: {}".format(
                    self.get_command_signature(command)
                    .replace(command.full_parent_name, "")
                    .strip(),
                    command.description or command.help,
                )
            )

        embed = discord.Embed(color=self.context.bot.color)
        embed.description = "{}\n\nSubcommand:\n{}".format(
            self.common_command_formatting(group), "\n".join(fields)
        )
        embed.set_footer(text="Cog: {}".format(command.cog_name))

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
    async def uptime(self, ctx):
        """Tells you how long the bot has been up for."""

        delta_uptime = datetime.utcnow() - self.bot.launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        
        await ctx.send(f"Uptime: `{days}d, {hours}h, {minutes}m, {seconds}s`")

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
    @commands.cooldown(rate=1, per=30.0, type=commands.BucketType.user)
    async def lmddgtfy(self, ctx, *, keywords: str):
        """Let me DuckDuckGo that for you."""

        await ctx.send("https://lmddgtfy.net/?q={}".format(keywords.replace(" ", "+")))

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

    async def get_last_commits(self, ctx, per_page=3):
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
                    "date": ctx.format_relative(date),
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
        memory_usage = self.process.memory_full_info().uss / 1024**2
        commits = await self.get_last_commits(ctx)

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
                        "[`{}`]({}) {} ({})".format(
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
