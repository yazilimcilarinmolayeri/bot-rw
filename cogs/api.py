import random
from io import BytesIO

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

    @commands.command(aliases=["sscan"])
    async def socialscan(self, ctx, account):
        """Querying username and email usage on online platforms."""

        platforms = [
            p.TWITTER,
            p.INSTAGRAM,
            p.REDDIT,
            p.GITHUB,
            p.GITLAB,
            p.SPOTIFY,
        ]

        async with ctx.typing():
            results = await execute_queries([account], platforms)

        embed = discord.Embed(color=self.bot.embed_color)
        embed.description = "\n\n".join(
            [
                f"**{r.query}** on **{r.platform}**: {r.message}\n"
                f"`(Success: {r.success}, Valid: {r.valid}, Available: {r.available})`"
                for r in results
            ]
        )

        await ctx.send(embed=embed)

    @commands.command(aliases=["ss"])
    async def screenshot(self, ctx, website):
        """Take a website screenshot."""

        website = website.replace("<", "").replace(">", "")
        website = website.replace(".html", "")

        if not website.startswith("http"):
            return await ctx.send("Not a valid website. Use http or https.")

        embed = discord.Embed(color=self.bot.embed_color)
        embed.description = f"Source: `{website}`\nInvoker: {ctx.author.mention}"
        embed.set_image(
            url=f"https://image.thum.io/get/width/2000/crop/1200/png/{website}"
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def quake(self, ctx, last: int = 1):
        """Show quake information from the Kandilli Observatory."""

        embeds = []
        max_request = 50
        headers = {"User-Agent": "bot-rw"}
        api_base = "https://api.berkealp.net/kandilli/index.php"
        params = {"last": max_request if last > max_request else last}

        async with ctx.typing():
            async with self.bot.web_client.get(
                api_base,
                ssl=True,
                params=params,
                headers=headers,
            ) as resp:
                data = await resp.json()

        for d in data:
            embed = discord.Embed(color=self.bot.embed_color)
            embed.description = (
                f"Latitude: `{d['Latitude'].split(';')[0]}`\n"
                f"Longitude: `{d['Longitude'].split(';')[0]}`\n"
                f"Magnitude-Depth: `{d['Magnitude']}-{d['Depth']} Km`\n"
                f"Datetime: `{d['Time']}`\n"
                f"Region: `{d['Region']}`"
            ).replace("&deg", "°")
            embed.set_thumbnail(url=d["MapImage"])
            embeds.append(embed)

        menu = menus.MenuPages(
            timeout=30,
            clear_reactions_after=True,
            source=EmbedSource(data=embeds),
        )
        await menu.start(ctx)

    @commands.command()
    async def pypi(self, ctx, package):
        """Show PyPi package informations."""

        async with ctx.typing():
            async with self.bot.web_client.get(
                f"https://pypi.org/pypi/{package}/json"
            ) as resp:
                if resp.status != 200:
                    return await ctx.send("Package not found.")
                data = await resp.json()
                data = data["info"]

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
    async def wiki(self, ctx, *, search):
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
            source=EmbedSource(data=embeds),
        )
        await menu.start(ctx)

    @commands.command()
    async def xkcd(self, ctx, num=None):
        """A webcomic of romance, sarcasm, math, and language."""

        api_base = "https://xkcd.com"

        async with ctx.typing():
            async with self.bot.web_client.get(f"{api_base}/info.0.json") as resp:
                data = await resp.json()

        if num == None:
            num = random.randint(1, data["num"])

        async with ctx.typing():
            async with self.bot.web_client.get(f"{api_base}/{num}/info.0.json") as resp:
                if resp.status != 200:
                    return await ctx.send("Invalid number.")
                data = await resp.json()

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

    async def send_activity(self, ctx, embed, data):
        embed.description = (
            "{}\n\n"
            "Type: `{}`\n"
            "Accessibility: `{}`\n"
            "Participants: `{}`\n"
            "Price: `{}`".format(
                data["activity"],
                data["type"].title(),
                data["accessibility"],
                data["participants"],
                data["price"],
            )
        )
        embed.set_footer(text="Key: {}".format(data["key"]))

        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True)
    async def bored(self, ctx):
        """Let's find you something to do."""

        url = "http://www.boredapi.com/api"

        async with ctx.typing():
            async with self.bot.web_client.get("{}/activity".format(url)) as resp:
                if resp.status != 200:
                    return await ctx.send(
                        "API connection error! Status code: `{}`".format(resp.status)
                    )
                data = await resp.json()

        embed = discord.Embed(color=self.bot.embed_color)
        await self.send_activity(ctx, embed, data)

    @bored.command(name="type")
    async def bored_type(self, ctx, type=None):
        """Find a random activity with a given type."""

        url = "http://www.boredapi.com/api"
        types = [
            "education",
            "recreational",
            "social",
            "diy",
            "charity",
            "cooking",
            "relaxation",
            "music",
            "busywork",
        ]
        embed = discord.Embed(color=self.bot.embed_color)

        if type == None:
            embed.description = "Activity types: {}".format(
                ", ".join(["`{}`".format(t) for t in types])
            )
            return await ctx.send(embed=embed)

        async with self.bot.web_client.get(
            "{}/activity".format(url), params={"type": type}
        ) as resp:
            if resp.status != 200:
                return await ctx.send(
                    "API connection error! Status code: `{}`".format(resp.status)
                )
            data = await resp.json()

        await self.send_activity(ctx, embed, data)

    @commands.command(aliases=["yn"])
    async def yesno(self, ctx):
        """Making a good decision might require some help."""

        url = "https://yesno.wtf/api"

        async with self.bot.web_client.get(url) as resp:
            if resp.status != 200:
                return await ctx.send(
                    "API connection error! Status code: `{}`".format(resp.status)
                )
            data = await resp.json()

        embed = discord.Embed(color=self.bot.embed_color)
        embed.description = data["answer"].upper()
        embed.set_image(url=data["image"])

        await ctx.send(embed=embed)
