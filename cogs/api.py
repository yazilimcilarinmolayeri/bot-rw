# -*- coding: utf-8 -*-

import aiowiki
import discord
from utils import paginator
from discord.ext import commands, menus


def setup(bot):
    bot.add_cog(API(bot))


class API(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["deprem"])
    async def quake(self, ctx, last=1):
        """"""

        embeds = []

        async with self.bot.session.get(
            "https://api.berkealp.net/kandilli/index.php",
            params={"last": last},
        ) as resp:
            if resp.status != 200:
                return await ctx.send("API not found!")
            data = await resp.json()

        for d in data:
            embed = discord.Embed(color=self.bot.color)
            date, time = d["Time"].split(" ")
            embed.description = (
                "Tarih: `{}`\n"
                "Saat: `{}`\n"
                "Enlem: `{}`\n"
                "Boylam: `{}`\n"
                "Bölge: `{}`\n"
                "Büyüklük: `{}` "
                "Derinlik: `{} Km`".format(
                    date,
                    time,
                    d["Latitude"].split(";")[0],
                    d["Longitude"].split(";")[0],
                    d["Region"],
                    d["Magnitude"],
                    d["Depth"],
                ).replace("&deg", "°")
            )
            embed.set_thumbnail(url=d["MapImage"])
            embeds.append(embed)

        menu = menus.MenuPages(
            timeout=30,
            clear_reactions_after=True,
            source=paginator.EmbedSource(data=embeds),
        )
        await menu.start(ctx)

    @commands.command()
    async def pypi(self, ctx, package):
        """"""

        async with self.bot.session.get(
            f"https://pypi.org/pypi/{package}/json"
        ) as resp:
            if resp.status != 200:
                return await ctx.send("No package found :(")
            data = await resp.json()
            data = data["info"]

        try:
            project_urls = ", ".join(
                [
                    "[`{}`]({})".format(t, u)
                    for t, u in data["project_urls"].items()
                ]
            )
        except AttributeError:
            project_urls = "~"

        embed = discord.Embed(color=self.bot.color)
        embed.title = data["name"] + " | " + data["version"]
        embed.url = data["package_url"]
        embed.description = (
            "{}\n\n"
            "Lisans: `{}`\n"
            "Geliştirici: `{}` (`{}`)\n"
            "Bağlantılar: {}"
        ).format(
            data["summary"] or " ",
            data["license"] or " ",
            data["author"] or " ",
            data["author_email"] or " ",
            project_urls,
        )
        embed.set_thumbnail(url="https://i.imgur.com/u6YG9jm.png")

        await ctx.send(embed=embed)

    @commands.command(aliases=["viki"])
    async def wiki(self, ctx, *, search):
        """"""

        embeds = []

        async with ctx.typing():
            wiki = aiowiki.Wiki.wikipedia("tr")
            for page in await wiki.opensearch(search):
                embed = discord.Embed(colour=self.bot.color)
                embed.title = page.title
                embed.url = (await page.urls())[0].split("(")[0]
                embed.description = (await page.summary())[:2000] + "..."
                embeds.append(embed)

        menu = menus.MenuPages(
            timeout=30,
            clear_reactions_after=True,
            source=paginator.EmbedSource(data=embeds),
        )
        await menu.start(ctx)
