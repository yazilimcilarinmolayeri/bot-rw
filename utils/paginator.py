import discord
from discord.ext import menus


class PageSource(menus.ListPageSource):
    async def format_page(self, menu, entries):
        embed = discord.Embed(color=0x2F3136)
        embed.description = "".join(e for e in entries)

        if self.get_max_pages() > 1:
            embed.set_footer(
                text=f"Page {menu.current_page + 1}/{self.get_max_pages()}"
            )

        return embed


class EmbedSource(menus.ListPageSource):
    def __init__(self, data, footer=True):
        super().__init__(data, per_page=1)
        self.footer = footer
        self.data_length = len(data)

    async def format_page(self, menu, entry: discord.Embed):
        if self.footer and self.data_length > 1:
            entry.set_footer(
                text=f"Sayfa {menu.current_page + 1}/{self.get_max_pages()}"
            )

        return entry
