import discord
from discord.ext import commands


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return "<Context>"

    async def tick(self, opt, label):
        lookup = {
            True: "<:greentick:844255173085364234>",
            False: "<:redtick:844255173450006549>",
            None: "<:graytick:844255172901077052>",
        }
        emoji = lookup.get(bool(opt), "<:redtick:844255173450006549>")

        await self.send("{} | {}".format(emoji, label))

    async def show_help(self, command=None):
        cmd = self.bot.get_command("help")
        command = command or self.command.qualified_name

        await self.invoke(cmd, command=command)
