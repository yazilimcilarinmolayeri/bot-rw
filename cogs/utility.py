# -*- coding: utf-8 -*-

import os
import time
import inspect
import discord
from discord.ext import commands
from utils import time as util_time


def setup(bot):
    bot.add_cog(Utility(bot))


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.c = bot.config

    @commands.command(aliases=["u"])
    async def uptime(self, ctx):
        """Tells you how long the bot has been up for."""

        await ctx.send(
            "Uptime: `{}`".format(util_time.humanize(self.bot.uptime))
        )

    @commands.command(aliases=["p"])
    async def ping(self, ctx):
        """Used to test bot's response time."""

        before = time.monotonic()
        message = await ctx.send("Pinging...")
        ping = (time.monotonic() - before) * 1000

        await message.edit(content="Pong! `{}ms`".format(round(ping, 2)))

    @commands.command(aliases=["anket"])
    async def poll(self, ctx, question, *answers):
        """
        Anket oluşturur. En fazla 10 seçenek verebilirsin.
        
        Örnek:
            .poll "Mandalina sever misin ?"
            .poll "En sevdiğin meyve ?" Elma Armut Mandalina ...
        """

        embed = discord.Embed(color=self.bot.embed_color)
        embed.timestamp = datetime.utcnow()
        embed.title = f"\N{WHITE QUESTION MARK ORNAMENT} {question}"
        embed.set_footer(text=ctx.author, icon_url=ctx.author.avatar_url)

        if answers == ():
            msg = await ctx.send(embed=embed)
            await msg.add_reaction("\N{THUMBS UP SIGN}")
            await msg.add_reaction("\N{THUMBS DOWN SIGN}")
            await msg.add_reaction("\N{SHRUG}")

        elif len(answers) <= 10:
            inner = [f"{i}\u20e3 : {answers[i]}" for i in range(len(answers))]
            embed.description = "\n".join(inner)

            msg = await ctx.send(embed=embed)

            for i in range(len(answers)):
                await msg.add_reaction(f"{i}\u20e3")

        else:
            await ctx.send_help(ctx.command)
    
        
    @commands.command()
    @commands.cooldown(rate=1, per=60.0, type=commands.BucketType.user)
    async def feedback(self, ctx, *, content):
        """Gives feedback about the bot."""

        author = ctx.author
        channel = self.bot.get_channel(self.c.getint("Channel", "FEEDBACK_CHANNEL_ID"))

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
    @commands.has_permissions(manage_roles=True)
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
