import discord
from discord.ext import commands, menus
from tortoise import exceptions as tortoise_exceptions

from utils import models, paginator


async def setup(bot):
    await bot.add_cog(ReactionRole(bot))


class ReactionRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.MAX_ROLE = 15

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
                payload.channel_id, member, "Hey {member.mention}, role limit alert!"
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

        if template.is_active:
            await self._add_or_remove_role(payload, template.emoji_and_role_bindings)

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
        await ctx.send(f"New reaction role template has created. ID: `{template.pk}`")

    @template.command(name="list", aliases=["l"])
    async def template_list(self, ctx):
        """Shows the list of templates on the server."""

        embeds = []
        templates = await models.ReactionRoleTemplate.filter(guild_id=ctx.guild.id)

        if not len(templates):
            return await ctx.send("Template note found!")

        for template in templates:
            if template.channel_id:
                channel = self.bot.get_channel(template.channel_id)
                template_message = await channel.fetch_message(template.message_id)
                jump_message = f"Original: [Jump!]({template_message.jump_url})"
            else:
                jump_message = ""

            embed = discord.Embed(color=self.bot.embed_color)
            embed.description = (
                f"Title: `{template.embed_title}`\n"
                f"UUID: `{template.pk}`\n\n"
                f"{jump_message}"
            )
            embeds.append(embed)

        menu = menus.MenuPages(
            timeout=30,
            clear_reactions_after=True,
            source=paginator.EmbedSource(data=embeds),
        )
        await menu.start(ctx)

    @template.command(name="status")
    async def template_status(self, ctx, uuid: str):
        """Change a template status. On or off."""

        template = await models.ReactionRoleTemplate.get(pk=uuid, guild_id=ctx.guild.id)

        if template.is_active:
            template.is_active = False
        else:
            template.is_active = True

        await template.save()
        await ctx.send(f"Template status updated to `{template.is_active}`.")

    @template.command(name="title")
    async def template_title(self, ctx, uuid: str, *, embed_title: str):
        """Template title update."""

        await models.ReactionRoleTemplate.get(pk=uuid, guild_id=ctx.guild.id).update(
            embed_title=embed_title,
        )
        await ctx.send("Title updated.")

    @template.command(name="color")
    async def template_color(self, ctx, uuid: str, embed_color):
        """Template color update. It accepts in 0xff00ff format."""

        await models.ReactionRoleTemplate.get(pk=uuid, guild_id=ctx.guild.id).update(
            embed_color=self.bot.embed_color
            if embed_color.lower() == "default"
            else int(embed_color, 16)
        )

        await ctx.send("Color updated.")

    async def _update_embed(self, ctx, template: str):
        channel = self.bot.get_channel(template.channel_id)
        template_message = await channel.fetch_message(template.message_id)

        embed = discord.Embed(color=template.embed_color)
        await self._generate_embed(ctx, embed, template)

        await template_message.edit(embed=embed)
        await template_message.clear_reactions()

        async with ctx.typing():
            for emoji in template.emoji_and_role_bindings.keys():
                await template_message.add_reaction(emoji)

    @template.command(name="add", aliases=["a"])
    async def template_add(self, ctx, uuid: str, emoji: str, role: discord.Role):
        """Add reaction role binding to template."""

        template = await models.ReactionRoleTemplate.get(pk=uuid, guild_id=ctx.guild.id)

        if len(template.emoji_and_role_bindings) >= 20:
            return await ctx.send("Reaction limit warning!")

        template.emoji_and_role_bindings.update({emoji: role.id})
        await template.save()

        if template.message_id:
            await self._update_embed(ctx, template)

        await ctx.send("Added reaction role and updated template message.")

    @template.command(name="remove", aliases=["r"])
    @commands.has_permissions(manage_messages=True)
    async def template_remove(self, ctx, uuid: str, emoji: str):
        """Remove reaction role binding to template."""

        template = await models.ReactionRoleTemplate.get(pk=uuid, guild_id=ctx.guild.id)

        try:
            template.emoji_and_role_bindings.pop(emoji)
        except KeyError:
            return await ctx.send("Emoji not found in template.")

        await template.save()

        if template.message_id:
            await self._update_embed(ctx, template)

        await ctx.send("Removed reaction role and updated template message.")

    async def _generate_embed(self, ctx, embed: discord.Embed, template):
        description = []
        embed.set_author(name=template.embed_title)

        for emoji, role_id in template.emoji_and_role_bindings.items():
            role = ctx.guild.get_role(role_id)
            description.append(f"{emoji} **-** {role}")

        embed.description = "\n".join(description)

    @template.command(name="show")
    async def template_show(self, ctx, uuid: str):
        """Show reaction role template message for test."""

        template = await models.ReactionRoleTemplate.get(pk=uuid, guild_id=ctx.guild.id)

        embed = discord.Embed(color=template.embed_color)
        await self._generate_embed(ctx, embed, template)

        await ctx.send(embed=embed)

    @template.command(name="send")
    async def template_send(self, ctx, uuid: str, channel: discord.TextChannel):
        """Send reaction role template message to channel."""

        template = await models.ReactionRoleTemplate.get(pk=uuid, guild_id=ctx.guild.id)

        embed = discord.Embed(color=template.embed_color)
        await self._generate_embed(ctx, embed, template)
        template_message = await channel.send(embed=embed)

        template.channel_id = channel.id
        template.message_id = template_message.id

        async with ctx.typing():
            for emoji in template.emoji_and_role_bindings.keys():
                await template_message.add_reaction(emoji)
            await template.save()

        await ctx.send("Done.")

    @template.command(name="kill")
    async def template_kill(self, ctx, uuid: str):
        """Kill template on the server."""

        await models.ReactionRoleTemplate.get(pk=uuid).delete()
        await ctx.send("Template killed.")
