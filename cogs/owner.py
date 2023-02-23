import copy

from discord.ext import commands
from jishaku.codeblocks import codeblock_converter


async def setup(bot):
    await bot.add_cog(Owner(bot))


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.command(aliases=["r"])
    async def reload(self, ctx: commands.Context):
        """Reloads the given extension names."""

        command = self.bot.get_command("jsk reload")
        await command.__call__(ctx, list(self.bot.extensions.keys()))

    @commands.is_owner()
    @commands.command(aliases=["sh"])
    async def shell(self, ctx: commands.Context, *, codeblock: codeblock_converter):
        """Executes statements in the system shell."""

        command = self.bot.get_command("jsk shell")
        await command.__call__(ctx, argument=codeblock)

    @commands.is_owner()
    @commands.command()
    async def restart(self, ctx: commands.Context):
        """Restart bot deamon service."""

        codeblock: codeblock_converter = "sudo systemctl restart bot-rw.service"
        command = self.bot.get_command("jsk shell")
        await command.__call__(ctx, argument=codeblock)

    @commands.is_owner()
    @commands.command()
    async def pull(self, ctx: commands.Context):
        """Run git pull command."""

        command = self.bot.get_command("jsk git pull")
        await command.__call__(ctx)

    @commands.command()
    @commands.is_owner()
    async def do(self, ctx: commands.Context, times: int, *, command: str):
        """Runs a command multiple times in a row."""

        message = copy.copy(ctx.message)
        message.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(message, cls=type(ctx))

        for i in range(int(times)):
            await new_ctx.reinvoke()
