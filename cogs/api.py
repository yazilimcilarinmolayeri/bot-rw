# -*- coding: utf-8 -*-

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
        """
        """

        embeds = []

        async with self.bot.session.get(
            "https://api.berkealp.net/kandilli/index.php",
            params={"last": last},
        ) as resp:
            if resp.status != 200:
                return await ctx.send("No data found :(")
            data = await resp.json()

        for d in data:
            embed = discord.Embed(color=self.bot.color)
            embed.description = (
                f"**Bölge:** {d['Region']}\n"
                f"**Büyüklük:** {d['Magnitude']}\n"
                f"**Derinlik:** {d['Depth']} Km\n"
                f"**Zaman:** {d['Time']}"
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
        async with self.bot.session.get(
            f"https://pypi.org/pypi/{package}/json"
        ) as resp:
            if resp.status != 200:
                return await ctx.send("No package found :(")
            data = await resp.json()
            data = data["info"]

        try:
            project_urls = "\n".join(
                [f"[{t}]({u})" for t, u in data["project_urls"].items()]
            )
        except AttributeError:
            project_urls = "~"

        embed = discord.Embed(color=self.bot.color)
        embed.url = data["package_url"]
        embed.title = data["name"] + " | " + data["version"]
        embed.description = data["summary"] or "~"
        embed.add_field(name="Geliştirici", value=data["author"] or "~")
        embed.add_field(name="Lisans", value=data["license"] or "~")
        embed.add_field(name="Bağlantılar", value=project_urls)
        await ctx.send(embed=embed)
