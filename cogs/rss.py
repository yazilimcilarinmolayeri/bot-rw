# -*- coding: utf-8 -*-

import discord
import feedparser
from discord.ext import commands, tasks


def setup(bot):
    bot.add_cog(RSS(bot))


class Feed:
    name = ""
    url = ""
    last_modified = ""
    title = ""
    link = ""

    def __init__(self, name, url, link):
        self.name = name
        self.url = url
        self.link = link


class RSS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.FEEDS = []
        ###
        self.FEED_CHANNEL_ID = 689249768165474309
        self.FEED_FILE_PATH = "data/feed_file.txt"
        ###
        self.printer.start()

    def _save(self):
        pass

    async def _notify(self, feed):
        channel = self.bot.get_channel(self.FEED_CHANNEL_ID)
        await channel.send(f"\N{NEWSPAPER} **| {feed.title}**\n\n{feed.link}")

    def cog_unload(self):
        self.printer.cancel()

    @tasks.loop(seconds=59.0)
    async def printer(self):
        for f in self.FEEDS:
            d = feedparser.parse(f.url)

            if f.link != d.entries[0].link:
                f.last_modified = d.entries[0].updated
                f.title = d.entries[0].title
                f.link = d.entries[0].link

                print(f.name + "\n" + f.title)
                await self._notify(f)
            else:
                print(f"{f.name} check...")

    @printer.before_loop
    async def before_printer(self):
        with open(self.FEED_FILE_PATH) as f:
            for line in f:
                feed = line.split(";")
                self.FEEDS.append(Feed(feed[0], feed[1], feed[2].rstrip()))

        await self.bot.wait_until_ready()

    @commands.group(invoke_without_command=True)
    async def feed(self, ctx):
        pass

    @feed.command(name="add")
    async def feed_add(self, ctx):
        pass

    @feed.command(name="remove")
    async def feed_remove(self, ctx):
        pass

    @feed.command(name="clear")
    async def feed_clear(self, ctx):
        pass

    @feed.command(name="check")
    async def feed_check(self, ctx):
        pass
