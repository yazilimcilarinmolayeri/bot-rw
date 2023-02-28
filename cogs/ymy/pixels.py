import re

import discord
from discord.ext import commands


API_BASE_URL = "https://pixels.yazilimcilarinmolayeri.com"
PIXELS_TOKEN_RE = re.compile(r"[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+\=]*")


async def setup(bot):
    await bot.add_cog(Pixels(bot))


class Pixels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def find_token_in_message(self, msg: discord.Message):
        for match in PIXELS_TOKEN_RE.finditer(msg.content):
            headers = {"Authorization": f"Bearer {match[0]}"}

            async with self.bot.web_client.delete(
                f"{API_BASE_URL}/token", headers=headers
            ) as r:
                if r.status == 204:
                    return match[0]
        return

    async def take_action(self, msg: discord.Message, found_token: str):
        try:
            await msg.delete()
        except discord.NotFound:
            return

        await msg.channel.send(
            f"Hey {msg.author.mention}! Mesajınızda geçerli bir Pixels API anahtarı "
            "buldum ve anahtarı sizin için geçersiz hale getirdim.\nYeni bir anahtar "
            f"edinmek için <{API_BASE_URL}/authorize> adresine gidebilirsin."
        )

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if not msg.guild or msg.author.bot:
            return

        found_token = await self.find_token_in_message(msg)

        if found_token:
            await self.take_action(msg, found_token)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        await self.on_message(after)
