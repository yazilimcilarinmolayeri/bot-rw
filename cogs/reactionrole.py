import discord
from discord.ext import commands, menus
from tortoise import exceptions as tortoise_exceptions

from utils import models
from utils.paginator import EmbedSource


async def setup(bot):
    await bot.add_cog(ReactionRole(bot))


class ReactionRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.MAX_ROLE = bot.config.getint("reactionrole", "max_role")

    async def _clear_reaction(self, payload, member: discord.Member):
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        await message.remove_reaction(member=member, emoji=payload.emoji)

    async def _send_notification(
        self, channel_id: int, member: discord.Member, content: str
    ):
        try:
            await member.send(content)
        except discord.Forbidden:
            channel = self.bot.get_channel(channel_id)
            await channel.send(content, delete_after=3.0)

    async def _add_or_remove_role(self, payload, bindings: list):
        guild = self.bot.get_guild(payload.guild_id)
        member = await guild.fetch_member(payload.user_id)
        role = discord.utils.get(
            guild.roles,
            id=bindings.get(payload.emoji.name),
        )

        if member.bot:
            return

        if len(member.roles) >= self.MAX_ROLE:
            await self._clear_reaction(payload, member)
            return await self._send_notification(
                payload.channel_id,
                member,
                "Hey {member.mention}, role limit warning!",
            )

        if member.get_role(role.id) is not None:
            await self._clear_reaction(payload, member)
            await member.remove_roles(role)
            return await self._send_notification(
                payload.channel_id,
                member,
                f"Hey {member.mention}, `{role.name}` role has been removed.",
            )
        else:
            await self._clear_reaction(payload, member)
            await member.add_roles(role)
            return await self._send_notification(
                payload.channel_id,
                member,
                f"Hey {member.mention}, `{role.name}` role has been added.",
            )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        try:
            template = await models.ReactionRoleTemplate.get(
                guild_id=payload.guild_id,
                channel_id=payload.channel_id,
                message_id=payload.message_id,
            )
        except tortoise_exceptions.DoesNotExist:
            return

        if template.status:
            await self._add_or_remove_role(payload, template.bindings)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def templates(self, ctx):
        """Shows the list of templates on the server."""

        await self.bot.get_command("template list").__call__(ctx)

    @commands.group(invoke_without_command=True, aliases=["t"])
    @commands.has_permissions(manage_roles=True)
    async def template(self, ctx):
        """Manage the reaction role templates on the server."""

        pass

    @template.command(name="new", aliases=["n"])
    async def template_new(self, ctx):
        """Create a new reaction role template."""

        template = await models.ReactionRoleTemplate.create(guild_id=ctx.guild.id)
        await ctx.send(f"New template has created. ID: `{template.pk}`")

    @template.command(name="list", aliases=["l"])
    async def template_list(self, ctx):
        """Shows the list of templates on the server."""

        entries = []
        templates = await models.ReactionRoleTemplate.filter(guild_id=ctx.guild.id)

        if not len(templates):
            return await ctx.send("Template not found!")

        for template in templates:
            if template.channel_id:
                channel = self.bot.get_channel(template.channel_id)
                message = await channel.fetch_message(template.message_id)
                jump_message = f"Original: [Jump!]({message.jump_url})"
            else:
                jump_message = ""

            entries.append(
                f"Title: `{template.embed_title}`\n"
                f"Status: `{template.status}`\n"
                f"Total binding: `{len(template.bindings)}`\n"
                f"ID: `{template.pk}`\n\n"
                f"{jump_message}"
            )

        menu = menus.MenuPages(
            EmbedSource(entries, per_page=1), clear_reactions_after=True
        )
        await menu.start(ctx)

    @template.command(name="status")
    async def template_status(self, ctx, id: str):
        """Change a template status. True is active or False is deactive."""

        template = await models.ReactionRoleTemplate.get(pk=id, guild_id=ctx.guild.id)
        template.status = False if template.status else True
        await template.save()
        await ctx.send(f"Template status update to `{template.status}`.")

    async def _generate_embed(self, ctx, embed: discord.Embed, template):
        description = []
        embed.color = template.embed_color
        embed.set_author(name=template.embed_title)

        for emoji, role_id in template.bindings.items():
            role = ctx.guild.get_role(role_id)
            description.append(f"{emoji} → {role}")

        embed.description = "\n".join(description)

    async def _update_embed(self, ctx, template: str, title_or_color: bool = False):
        embed = discord.Embed()
        channel = self.bot.get_channel(template.channel_id)
        template_message = await channel.fetch_message(template.message_id)
        await self._generate_embed(ctx, embed, template)
        await template_message.edit(embed=embed)

        if not title_or_color:
            await template_message.clear_reactions()

            async with ctx.typing():
                for emoji in template.bindings.keys():
                    await template_message.add_reaction(emoji)

    @template.command(name="title")
    async def template_title(self, ctx, id: str, *, title: str):
        """Template title update."""

        template = await models.ReactionRoleTemplate.get(pk=id, guild_id=ctx.guild.id)
        template.embed_title = title

        if template.channel_id:
            await self._update_embed(ctx, template, title_or_color=True)

        await template.save()
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

    @template.command(name="color")
    async def template_color(self, ctx, id: str, color: str):
        """Template color update. It accepts in ff00ff format."""

        template = await models.ReactionRoleTemplate.get(pk=id, guild_id=ctx.guild.id)
        template.embed_color = int("0x" + color, 16)

        if template.channel_id:
            await self._update_embed(ctx, template, title_or_color=True)

        await template.save()
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

    @template.command(name="add", aliases=["a"])
    async def template_add(self, ctx, id: str, emoji: str, role: discord.Role):
        """Add reaction role binding to template."""

        template = await models.ReactionRoleTemplate.get(pk=id, guild_id=ctx.guild.id)

        if len(template.bindings) >= 20:
            return await ctx.send("Reaction limit warning!")

        template.bindings.update({emoji: role.id})
        await template.save()

        if template.message_id:
            await self._update_embed(ctx, template)

        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

    @template.command(name="remove", aliases=["r"])
    @commands.has_permissions(manage_messages=True)
    async def template_remove(self, ctx, id: str, emoji: str):
        """Remove reaction role binding to template."""

        template = await models.ReactionRoleTemplate.get(pk=id, guild_id=ctx.guild.id)

        try:
            template.bindings.pop(emoji)
        except KeyError:
            return await ctx.message.send("Emoji not found in template.")

        await template.save()

        if template.message_id:
            await self._update_embed(ctx, template)

        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

    @template.command(name="show")
    async def template_show(self, ctx, id: str):
        """Show reaction role template message for test."""

        embed = discord.Embed()
        template = await models.ReactionRoleTemplate.get(pk=id, guild_id=ctx.guild.id)
        await self._generate_embed(ctx, embed, template)
        await ctx.send(embed=embed)

    @template.group(name="send", invoke_without_command=True)
    async def template_send(self, ctx, id: str, channel: discord.TextChannel):
        """Send reaction role template message to channel."""
        
        embed = discord.Embed()
        template = await models.ReactionRoleTemplate.get(pk=id, guild_id=ctx.guild.id)
        await self._generate_embed(ctx, embed, template)
        template_message = await channel.send(embed=embed)
        template.channel_id = channel.id
        template.message_id = template_message.id

        async with ctx.typing():
            for emoji in template.bindings.keys():
                await template_message.add_reaction(emoji)
            await template.save()

        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

    @template_send.command(name="all")
    async def template_send_all(self, ctx, channel: discord.TextChannel):
        """Send all reaction role templates to channel."""

        embed = discord.Embed()
        templates = await models.ReactionRoleTemplate.filter(guild_id=ctx.guild.id)

        for template in templates:
            await self._generate_embed(ctx, embed, template)
            template_message = await channel.send(embed=embed)
            template.channel_id = channel.id
            template.message_id = template_message.id

            async with ctx.typing():
                for emoji in template.bindings.keys():
                    await template_message.add_reaction(emoji)
                await template.save()

        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

    @template.command(name="kill")
    async def template_kill(self, ctx, id: str):
        """Kill template on the server and database."""

        await models.ReactionRoleTemplate.get(pk=id).delete()
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
