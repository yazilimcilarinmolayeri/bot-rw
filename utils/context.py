from discord.ext import commands


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return "<Context>"

    def mention(self, user_id):
        return f"<@{user_id}>"

    async def show_help(self, command=None):
        cmd = self.bot.get_command("help")
        command = command or self.command.qualified_name

        await self.invoke(cmd, command=command)
