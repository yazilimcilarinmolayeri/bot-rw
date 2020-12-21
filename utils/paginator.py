import discord
from discord.ext import menus


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
