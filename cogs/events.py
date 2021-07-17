# -*- coding: utf-8 -*-

import sys
import arrow
import discord
import traceback
from io import StringIO
from datetime import datetime
from discord.ext import commands
from tortoise.query_utils import Q
from utils import models, functions
from discord.ext import commands, menus
from discord import Status, ActivityType


def setup(bot):
    bot.add_cog(Events(bot))


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.c = bot.config

    async def _change_presence(self):
        guild = self.bot.get_guild(self.c.getint("Guild", "DEFAULT_GUILD_ID"))

        try:
            bots = sum(m.bot for m in guild.members)
            humans = guild.member_count - bots
            name = "{} + {}".format(humans, bots)
        except AttributeError:
            name = "?"

        await self.bot.change_presence(
            activity=discord.Activity(
                type=ActivityType.watching,
                name="{} üyeyi".format(name),
            ),
            status=Status.idle,
        )

    @commands.Cog.listener()
    async def on_ready(self):
        if not hasattr(self, "uptime"):
            self.bot.uptime = arrow.utcnow()

        print(
            "{} (ID: {})\ndiscord.py version: {}".format(
                self.bot.user, self.bot.user.id, discord.__version__
            )
        )

        await models.init()  # database init
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
            channel = self.bot.get_channel(
                self.c.getint("Channel", "MENTION_LOG_CHANNEL_ID")
            )

            embed = discord.Embed(color=self.bot.color)
            embed.description = message.content
            embed.set_author(name=author, icon_url=author.avatar.url)
            embed.add_field(
                name="Bahsetme Bilgisi",
                value="Kanal: {} `(ID: {})`\n"
                "Sunucu: `{} (ID: {})`\n\n"
                "[`Mesaja zıpla!`]({})".format(
                    message.channel.mention,
                    message.channel.id,
                    author.guild,
                    author.guild.id,
                    message.jump_url,
                ),
            )
            embed.set_footer(text="ID: {}".format(author.id))

            if message.attachments:
                attachment_url = message.attachments[0].url
                embed.set_image(url=attachment_url)

            await channel.send(embed=embed)

    @commands.Cog.listener(name="on_message")
    async def on_dm_message(self, message):
        author = message.author

        if author.bot:
            return

        if message.guild is None:
            channel = self.bot.get_channel(
                self.c.getint("Channel", "DM_LOG_CHANNEL_ID")
            )

            embed = discord.Embed(color=self.bot.color)
            embed.description = message.content
            embed.set_author(name=author, icon_url=author.avatar.url)
            embed.set_footer(text="ID: {}".format(author.id))

            if message.attachments:
                attachment_url = message.attachments[0].url
                embed.set_image(url=attachment_url)

            await channel.send(embed=embed)

    async def update_emoji_stats(self, guild, author, message):
        custom_emojis = functions.custom_emoji_counter(guild, message)

        if not len(custom_emojis):
            return

        data = await models.EmojiUsageStat.filter(guild_id=guild.id).values()

        # TODO: Design optimized and combine with 2nd for loop
        for d in data:
            for emoji, amount in custom_emojis.items():
                try:
                    if d["emoji_id"] == emoji.id:
                        await models.EmojiUsageStat.filter(
                            Q(guild_id=guild.id)
                            & Q(user_id=author.id)
                            & Q(emoji_id=emoji.id)
                        ).update(
                            amount=d["amount"] + amount,
                            last_usage=datetime.utcnow(),
                        )
                except KeyError:
                    await models.EmojiUsageStat.create(
                        guild_id=guild.id,
                        user_id=author.id,
                        emoji_id=emoji.id,
                        amount=0,
                        last_usage=datetime.utcnow(),
                    )

        for emoji, amount in custom_emojis.items():
            try:
                if not emoji.id in [d["emoji_id"] for d in data]:
                    await models.EmojiUsageStat.create(
                        guild_id=guild.id,
                        user_id=author.id,
                        emoji_id=emoji.id,
                        amount=amount,
                        last_usage=datetime.utcnow(),
                    )
            except AttributeError:
                continue

    @commands.Cog.listener(name="on_message")
    async def on_emoji(self, message):
        guild = message.guild
        author = message.author

        await self.update_emoji_stats(guild, author, message)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        b_custom_emojis = functions.custom_emoji_counter(before.guild, before)
        a_custom_emojis = functions.custom_emoji_counter(after.guild, after)

        if len(a_custom_emojis) > len(b_custom_emojis):
            await self.update_emoji_stats(after.guild, after.author, after)

    # @commands.Cog.listener(name="on_user_update")
    async def on_update_avatar(self, before, after):
        user = after
        b_avatar_key = before.avatar.key
        a_avatar_key = after.avatar.key

        if b_avatar_key == a_avatar_key:
            return

        avatar_url = user.avatar.url[: user.avatar.url.find("?")]
        channel = self.bot.get_channel(
            self.c.getint("Channel", "AVATAR_LOG_CHANNEL_ID")
        )

        embed = discord.Embed(color=self.bot.color)
        embed.set_author(name=user)
        embed.set_image(url=avatar_url)
        embed.set_footer(text="ID: {}".format(user.id))

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(
            error,
            (
                discord.Forbidden,
                commands.CommandNotFound,
                commands.DisabledCommand,
                menus.MenuError,
            ),
        ):
            return

        if isinstance(error, commands.errors.CommandOnCooldown):
            return await ctx.send(
                "Komut bekleme modunda! `{}sn` sonra tekrar dene.".format(
                    round(error.retry_after)
                )
            )

        if isinstance(
            error,
            (
                commands.CheckFailure,
                commands.errors.BadArgument,
                commands.errors.MissingRequiredArgument,
            ),
        ):
            # Warning reaction
            return await ctx.message.add_reaction("\U000026a0")

        channel = self.bot.get_channel(
            self.c.getint("Channel", "ERROR_LOG_CHANNEL_ID")
        )

        error = error.original
        exc = "".join(
            traceback.format_exception(
                type(error), error, error.__traceback__, chain=False
            )
        )

        # Interrobang reaction
        await ctx.message.add_reaction("\U00002049")
        await channel.send(
            content="In `{}`: `{}`: `{}`".format(
                ctx.command.qualified_name,
                error.__class__.__name__,
                error,
            ),
            file=discord.File(
                StringIO(exc),
                filename="traceback.txt",
            ),
        )
