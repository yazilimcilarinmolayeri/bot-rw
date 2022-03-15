import sys
import traceback
from io import StringIO
from datetime import datetime

import discord
from tortoise.query_utils import Q
from discord import Status, ActivityType
from discord.ext import commands, menus, tasks

from utils import models, functions


async def setup(bot):
    await bot.add_cog(Events(bot))


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.launch_time = datetime.utcnow()

        print(
            "┬ ┬┌┬┐┬ ┬┌┐ ┌─┐┌┬┐  ┬─┐┬ ┬\n"
            "└┬┘│││└┬┘├┴┐│ │ │───├┬┘│││\n"
            " ┴ ┴ ┴ ┴ └─┘└─┘ ┴   ┴└─└┴┘\n"
            f"Bot name: {self.bot.user}\n"
            f"ID: {self.bot.user.id}\n"
            f"Library version: {discord.__version__}"
        )

        await models.init()  # Database init

    @commands.Cog.listener()
    async def on_member_join(self, member):
        pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        pass

    @commands.Cog.listener(name="on_message")
    async def on_bot_mention(self, message):
        author = message.author
        channel = self.bot.get_channel(self.bot.config["log"]["dm_mention_channel_id"])

        if author.bot:
            return

        if message.guild is None:
            embed = discord.Embed(color=self.bot.color)
            embed.description = message.content
            embed.set_author(name=author, icon_url=author.avatar.url)
            embed.set_footer(text=f"ID: {author.id}")

            if message.attachments:
                attachment_url = message.attachments[0].url
                embed.set_image(url=attachment_url)

            await channel.send(embed=embed)

        if self.bot.user.mentioned_in(message) and message.mention_everyone is False:
            embed = discord.Embed(color=self.bot.color)
            embed.description = (
                f"{message.content}\n\n"
                f"Channel: {message.channel.mention} "
                f"(`{message.channel.id}`)\n"
                f"Guild: {author.guild} "
                f"(`{author.guild.id}`)\n\n"
                f"[`Jump message!`]({message.jump_url})"
            )
            embed.set_author(name=author, icon_url=author.avatar.url)
            embed.set_footer(text=f"ID: {author.id}")

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

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(
            error,
            (
                discord.Forbidden,
                commands.CommandNotFound,
                commands.DisabledCommand,
                menus.MenuError,
                discord.errors.HTTPException,
            ),
        ):
            return

        if isinstance(error, commands.errors.CommandOnCooldown):
            return await ctx.send(
                f"Please wait `{round(error.retry_after)}` second to use this command again."
            )

        if isinstance(error, commands.errors.MissingRequiredArgument):
            # TODO: Better formatted output
            return await ctx.send(error)

        if isinstance(error, commands.errors.BadArgument):
            return await ctx.send(str(error).replace('"', "`"))

        if isinstance(error, commands.CheckFailure):
            return await ctx.message.add_reaction("\U0001f608")

        error = error.original
        exc = "".join(
            traceback.format_exception(
                type(error), error, error.__traceback__, chain=False
            )
        )

        channel = self.bot.get_channel(self.bot.config["log"]["error_channel_id"])

        await ctx.message.add_reaction("\U00002049")
        await channel.send(
            content=(
                f"In `{ctx.command.qualified_name}`: "
                f"`{error.__class__.__name__}`: `{error}`"
            ),
            file=discord.File(
                StringIO(exc),
                filename="traceback.txt",
            ),
        )
