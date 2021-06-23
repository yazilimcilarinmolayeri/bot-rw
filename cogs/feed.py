# -*- coding: utf-8 -*-

import json
import string
import random
import discord
import feedparser
from io import StringIO
from datetime import datetime
from tortoise import tortoise_exceptions
from discord.ext import commands, tasks, menus
from utils import paginator, models, functions, time as util_time


def setup(bot):
    bot.add_cog(Feed(bot))


class Feed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.feed_checker.start()

    def cog_unload(self):
        self.feed_checker.cancel()

    async def send_entry(self, guild_id, channel_id, entry):
        guild = self.bot.get_guild(guild_id)
        channel = guild.get_channel(channel_id)

        await channel.send("{}\n> {}".format(entry.title, entry.link))

    @tasks.loop(minutes=5.0)
    async def feed_checker(self):
        try:
            feeds = await models.Feed.all()
        except tortoise_exceptions.ConfigurationError:
            return

        for feed in feeds:
            parse = feedparser.parse(feed.feed_url)

            try:
                last_entry = parse.entries[0]
            except KeyError:
                last_entry = feed.last_entry.link

            if feed.last_entry_url == last_entry.link:
                return

            await self.send_entry(feed.guild_id, feed.channel_id, last_entry)
            await models.Feed.get(pk=feed.feed_id).update(
                last_entry_url=last_entry.link,
                last_entry=datetime.utcnow(),
            )

    @feed_checker.before_loop
    async def before_feed_checker(self):
        await self.bot.wait_until_ready()

    @commands.command()
    async def feeds(self, ctx):
        """Shows the list of feeds on the server."""

        embeds = []
        guild = ctx.guild
        data = await models.Feed.filter(guild_id=guild.id).values()
        total = sum([1 for d in data])

        if not len(data):
            return await ctx.send("Kayıt bulunamadı!")

        for data in functions.list_to_matrix(data, col=5):
            embed = discord.Embed(color=self.bot.color)
            embed.set_author(name=guild, icon_url=guild.icon.url)
            embed.description = "{}\n{}".format(
                "\n".join(
                    [
                        "ID: `{0}`\n"
                        "Kanal: {1} `(En son: {2})`\n"
                        "Adres: [`{3}`]({3})\n".format(
                            d["feed_id"],
                            guild.get_channel(d["channel_id"]).mention,
                            util_time.humanize(d["last_entry"]),
                            d["feed_url"],
                        )
                        for d in data
                    ]
                ),
                "Toplam: `{}`".format(total),
            )
            embeds.append(embed)

        menu = menus.MenuPages(
            timeout=30,
            clear_reactions_after=True,
            source=paginator.EmbedSource(data=embeds),
        )
        await menu.start(ctx)

    @commands.group(invoke_without_command=True, aliases=["fm"])
    async def feedmanager(self, ctx):
        """Manage the feeds on the server."""

        command = self.bot.get_command("feeds")
        await command.__call__(ctx=ctx)

    @feedmanager.command(name="add")
    @commands.has_permissions(manage_messages=True)
    async def feedmanager_add(self, ctx, channel: discord.TextChannel, url):
        """Adds a feed to the channel."""

        guild = ctx.guild
        message = await ctx.send("RSS/Feed ekleniyor...")
        parse = feedparser.parse(url)

        try:
            if parse.status != 200 and parse.status != 301:
                return await message.edit(content="Geçersiz bağlantı!")
        except AttributeError:
            return await message.edit(content="Geçersiz bağlantı!")

        last_entry = parse.entries[0]

        await models.Feed.create(
            feed_id="".join(
                random.choices(string.ascii_lowercase + string.digits, k=8)
            ),
            guild_id=guild.id,
            channel_id=channel.id,
            feed_url=url,
            last_entry_url=last_entry.link,
            last_entry=datetime.utcnow(),
        )
        await message.edit(content="RSS/Feed eklendi.")
        await self.send_entry(guild.id, channel.id, last_entry)

    @feedmanager.command(name="remove")
    @commands.has_permissions(manage_messages=True)
    async def feedmanager_remove(self, ctx, feed_id):
        """Removes the feed from the channel."""

        await models.Feed.get(pk=feed_id).delete()
        await ctx.send("RSS/Feed kaldırıldı.")

    @feedmanager.command(name="backup")
    async def feedmanager_backup(self, ctx):
        """Takes JSON backup of feed list."""

        backup = {}
        feeds = await models.Feed.all()

        for feed in feeds:
            feed_info = {}
            feed_info["guild_id"] = feed.guild_id
            feed_info["channel_id"] = feed.channel_id
            feed_info["feed_url"] = feed.feed_url
            backup[feed.feed_id] = feed_info

        await ctx.send(
            file=discord.File(
                fp=StringIO(json.dumps(backup, indent=4)),
                filename="backup.json",
            )
        )
