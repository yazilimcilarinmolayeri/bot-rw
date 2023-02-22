import discord
from discord.ext import menus


class EmbedSource(menus.ListPageSource):
    async def format_page(self, menu, entry: discord.Embed):
        if self.get_max_pages() > 1:
            entry.set_footer(
                text=f"Page {menu.current_page + 1}/{self.get_max_pages()}"
            )

        return entry


class DescriptionSource(menus.ListPageSource):
    def __init__(self, entries, per_page, title: str = None):
        super().__init__(entries=entries, per_page=per_page)
        self.title = title

    async def format_page(self, menu, entries: list):
        embed = discord.Embed(color=0x2F3136)

        if self.title is not None:
            embed.title = self.title

        embed.description = "".join(e for e in entries)

        if self.get_max_pages() > 1:
            embed.set_footer(
                text=f"Page {menu.current_page + 1}/{self.get_max_pages()}"
            )

        return embed
