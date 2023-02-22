import random

import aiowiki
import discord
from discord.ext import commands, menus
from socialscan.util import Platforms as p
from socialscan.util import execute_queries

from utils.paginator import EmbedSource


async def setup(bot):
    await bot.add_cog(API(bot))


class API(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.socialscan_platforms = [
            p.TWITTER,
            p.INSTAGRAM,
            p.REDDIT,
            p.GITHUB,
            p.GITLAB,
            p.SPOTIFY,
        ]

        self.ss_api_base = "https://image.thum.io/get/width/2000/crop/1200/png"
        self.kandilli_api_base = "https://api.berkealp.net/kandilli/index.php"
        self.pypi_api_base = "https://pypi.org/pypi"
        self.xkcd_api_base = "https://xkcd.com"

    @commands.command(aliases=["sscan"])
    async def socialscan(self, ctx: commands.Context, account: str):
        """Querying username and email usage on online platforms."""

        async with ctx.typing():
            results = await execute_queries([account], self.socialscan_platforms)

        embed = discord.Embed(color=self.bot.embed_color, title="SocialScan Result")
        embed.description = "\n\n".join(
            [
                f"**{r.query}** on **{r.platform}**: {r.message}\n"
                f"`(Success: {r.success}, Valid: {r.valid}, Available: {r.available})`"
                for r in results
            ]
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["ss"])
    async def screenshot(self, ctx: commands.Context, website: str):
        """Take a website screenshot."""

        website = website.replace("<", "").replace(">", "")
        website = website.replace(".html", "")

        if not website.startswith("http"):
            return await ctx.send("Not a valid website. Use http or https.")

        embed = discord.Embed(color=self.bot.embed_color, title="Website Screenshot")
        embed.description = f"Source: `{website}`\nInvoker: {ctx.author.mention}"
        embed.set_image(url=f"{self.ss_api_base}/{website}")
        await ctx.send(embed=embed)

    @commands.command()
    async def quake(self, ctx: commands.Context, last: int = 1):
        """Show quake information from the Kandilli Observatory."""

        embeds = []
        max_request = 50

        async with ctx.typing():
            async with self.bot.web_client.get(
                self.kandilli_api_base,
                ssl=True,
                headers={"User-Agent": "bot-rw"},
                params={"last": max_request if last > max_request else last},
            ) as r:
                response = await r.json()

        for data in response:
            embed = discord.Embed(
                color=self.bot.embed_color, title="Kandilli Quake Info"
            )
            embed.description = (
                f"Latitude: `{data['Latitude'].split(';')[0]}`\n"
                f"Longitude: `{data['Longitude'].split(';')[0]}`\n"
                f"Region: `{data['Region']}`\n"
                f"Magnitude - Depth: `{data['Magnitude']} - {data['Depth']} Km`\n"
                f"Datetime: `{data['Time']}`"
            ).replace("&deg", "°")
            embed.set_image(url=data["MapImage"])
            embeds.append(embed)

        menu = menus.MenuPages(
            timeout=30,
            clear_reactions_after=True,
            source=EmbedSource(embeds, per_page=1),
        )
        await menu.start(ctx)

    @commands.command()
    async def pypi(self, ctx: commands.Context, package: str):
        """Show PyPi package informations."""

        async with ctx.typing():
            async with self.bot.web_client.get(
                f"{self.pypi_api_base}/{package}/json"
            ) as r:
                if r.status != 200:
                    return await ctx.send("Package not found.")
                response = await r.json()
                data = response["info"]

        try:
            project_urls = ", ".join(
                [f"[{title}]({url})" for title, url in data["project_urls"].items()]
            )
        except AttributeError:
            project_urls = "?"

        embed = discord.Embed(color=self.bot.embed_color)
        embed.title = f"{data['name']} | {data['version']}"
        embed.url = data["package_url"]
        embed.description = (
            f"{data['summary'] or '?'}\n\n"
            f"License: `{data['license'] or '?'}`\n"
            f"Author(s): `{data['author'] or '?'} "
            f"({data['author_email'] or '?'})`\n"
            f"Project links: {project_urls}"
        )
        embed.set_thumbnail(url="https://i.imgur.com/u6YG9jm.png")
        await ctx.send(embed=embed)

    @commands.command()
    async def wiki(self, ctx: commands.Context, *, search: str):
        """Search the Turkish Wikipedia."""

        embeds = []

        async with ctx.typing():
            wiki = aiowiki.Wiki.wikipedia("tr")

            for page in await wiki.opensearch(search):
                embed = discord.Embed(colour=self.bot.embed_color)
                embed.title = page.title
                embed.url = (await page.urls())[0].split("(")[0]
                embed.description = (await page.summary())[:2000] + "..."
                embeds.append(embed)

        menu = menus.MenuPages(
            timeout=30,
            clear_reactions_after=True,
            source=EmbedSource(embeds, per_page=1),
        )
        await menu.start(ctx)

    @commands.command()
    async def xkcd(self, ctx: commands.Context, number: int = None):
        """A webcomic of romance, sarcasm, math, and language."""

        async with ctx.typing():
            async with self.bot.web_client.get(
                f"{self.xkcd_api_base}/info.0.json"
            ) as r:
                data = await r.json()

        if number is None:
            number = random.randint(1, data["num"])

        async with ctx.typing():
            async with self.bot.web_client.get(
                f"{self.xkcd_api_base}/{number}/info.0.json"
            ) as r:
                if r.status != 200:
                    return await ctx.send("Invalid number.")
                data = await r.json()

        embed = discord.Embed(color=self.bot.embed_color)
        embed.title = data["title"]
        embed.description = data["alt"]
        embed.set_image(url=data["img"])
        embed.set_footer(
            text="{} • {}/{}/{}".format(
                data["num"], data["day"], data["month"], data["year"]
            )
        )
        await ctx.send(embed=embed)
