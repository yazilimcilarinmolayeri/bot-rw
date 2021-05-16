# -*- coding: utf-8 -*-

import discord
import traceback
from utils import config
from datetime import datetime
from discord.ext import commands
from discord.ext.commands import errors


def setup(bot):
    bot.add_cog(Events(bot))


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _change_presence(self):
        guild = self.bot.get_guild(config.DEFAULT_GUILD_ID)
        bots = sum(m.bot for m in guild.members)
        humans = guild.member_count - bots

        await self.bot.change_presence(
            activity=discord.Activity(
                type=config.ACTIVITY_TYPE,
                name=f"{humans:,d} + {bots} üyeyi",
            ),
            status=config.STATUS_TYPE,
        )

    @commands.Cog.listener()
    async def on_ready(self):
        if not hasattr(self, "uptime"):
            self.bot.uptime = datetime.now()

        print(
            f"{self.bot.user} (ID: {self.bot.user.id})\n"
            f"discord.py version: {discord.__version__}"
        )

        await self._change_presence()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self._change_presence()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self._change_presence()

    @commands.Cog.listener(name="on_message")
    async def on_bot_mention(self, message):
        author = message.author

        if (
            self.bot.user.mentioned_in(message)
            and message.mention_everyone is False
        ):
            channel = self.bot.get_channel(config.MENTION_LOG_CHANNEL_ID)

            embed = discord.Embed(color=self.bot.color)
            embed.description = message.content
            embed.set_author(name=author, icon_url=author.avatar_url)
            embed.add_field(
                name="Bahsetme Bilgisi",
                value="`#{}` (`{}`)\n"
                "`{}` (`{}`)\n\n"
                "[`Mesaja zıpla!`]({})".format(
                    message.channel.name,
                    message.channel.id,
                    author.guild,
                    author.guild.id,
                    message.jump_url,
                ),
            )
            embed.set_footer(text=f"ID: {author.id}")

            if message.attachments:
                attachment_url = message.attachments[0].url
                embed.set_image(url=attachment_url)

            await channel.send(embed=embed)

    @commands.Cog.listener(name="on_message")
    async def on_dm_message(self, message):
        author = message.author

        if message.guild is None:
            channel = self.bot.get_channel(config.DM_LOG_CHANNEL_ID)

            embed = discord.Embed(color=self.bot.color)
            embed.description = message.content
            embed.set_author(name=author, icon_url=author.avatar_url)
            embed.set_footer(text=f"ID: {author.id}")

            if message.attachments:
                attachment_url = message.attachments[0].url
                embed.set_image(url=attachment_url)

            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, err):
        msa = errors.MissingRequiredArgument

        if isinstance(err, commands.CommandInvokeError):
            original = err.original

            if not isinstance(original, discord.HTTPException):
                # TODO: Add logger
                print(
                    "In {}:".format(ctx.command.qualified_name),
                    file=sys.stderr,
                )
                traceback.print_tb(original.__traceback__)
                print(
                    "{}: {}".format(original.__class__.__name__, original),
                    file=sys.stderr,
                )

        if isinstance(err, commands.CheckFailure):
            await ctx.send(
                "Bu komutu kullanabilmek için yeterli yetkiye sahip değilsin!"
            )

        if isinstance(err, msa) or isinstance(err, errors.BadArgument):
            helper = (
                str(ctx.invoked_subcommand)
                if ctx.invoked_subcommand
                else str(ctx.command)
            )
            await ctx.send_help(helper)

        if isinstance(err, errors.CommandOnCooldown):
            await ctx.send(
                "Bu komut bekleme modunda! `{}`sn sonra tekrar dene.".format(
                    round(err.retry_after)
                )
            )
