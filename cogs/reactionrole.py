import discord
from discord.utils import get
from discord.ext import commands
from tortoise.query_utils import Q
from tortoise import exceptions as tortoise_exceptions

from utils import models, functions


async def setup(bot):
    await bot.add_cog(ReactionRole(bot))


class ReactionRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.MAX_ROLE = 15

    async def _clear_reaction(self, payload, member):
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        await message.remove_reaction(emoji=payload.emoji, member=member)

    async def _send_message(self, payload, member, message):
        channel = self.bot.get_channel(payload.channel_id)

        try:
            await member.send(message)
        except discord.Forbidden:
            await channel.send(content=message, delete_after=3.0)

    async def add_or_remove_role(self, payload, template):
        guild = self.bot.get_guild(payload.guild_id)
        member = await guild.fetch_member(payload.user_id)

        if member.bot:
            return

        rr = await models.ReactionRoles.get(emoji=payload.emoji)
        role = get(guild.roles, id=rr.role_id)

        if role.id in [r.id for r in member.roles]:
            await member.remove_roles(role)
            await self._clear_reaction(payload, member)
            return await self._send_message(
                payload,
                member,
                "`{}`, `{}` role has been __removed__.".format(member, role.name),
            )
        else:
            if len(member.roles) - 1 >= self.MAX_ROLE:
                await self._clear_reaction(payload, member)
                return await self._send_message(
                    payload,
                    member,
                    "{}, you can take a max of `{}` roles.".format(
                        member.mention, self.MAX_ROLE
                    ),
                )
            else:
                await member.add_roles(role)
                await self._clear_reaction(payload, member)
                return await self._send_message(
                    payload,
                    member,
                    "`{}`, `{}` role has been __added__.".format(member, role.name),
                )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild_id = payload.guild_id
        channel_id = payload.channel_id
        message_id = payload.message_id

        try:
            template = await models.Templates.get(
                guild_id=guild_id, channel_id=channel_id, message_id=message_id
            )
        except tortoise_exceptions.DoesNotExist:
            return

        if template.status:
            await self.add_or_remove_role(payload, template)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        pass

    @commands.command(aliases=["temps"])
    @commands.has_permissions(manage_roles=True)
    async def templates(self, ctx):
        """Shows the list of templates on the server."""

        command = self.bot.get_command("rrmanager list")
        await command.__call__(ctx)

    @commands.group(invoke_without_command=True, aliases=["rrm"])
    @commands.has_permissions(manage_roles=True)
    async def rrmanager(self, ctx):
        """Manage the reaction role on the server."""

        pass

    @rrmanager.command(name="new")
    async def rrmanager_new(self, ctx):
        """Create a new reaction role template."""

        template_id = functions.random_id()

        await models.Templates.create(id=template_id, guild_id=ctx.guild.id)
        await ctx.send(
            "New reaction role template has created. ID: `{}`".format(
                template_id,
            )
        )

    @rrmanager.command(name="list")
    async def rrmanager_list(self, ctx):
        """Shows the list of templates on the server."""

        templates = await models.Templates.filter(Q(guild_id=ctx.guild.id))

        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_author(name="Reaction Role Templates")
        embed.description = (
            "{}\n\nAll: `{}`".format(
                ", ".join(["`{}`".format(t.id) for t in templates]),
                len(templates),
            )
            if len(templates)
            else "None"
        )

        await ctx.send(embed=embed)

    @rrmanager.command(name="info")
    async def rrmanager_info(self, ctx, template_id):
        """Shows info about a template."""

        template = await models.Templates.get(id=template_id, guild_id=ctx.guild.id)

        if template.channel_id:
            channel = self.bot.get_channel(template.channel_id)
            message = await channel.fetch_message(template.message_id)
            jump_message = "[`Jump`]({})".format(message.jump_url)
        else:
            jump_message = "`None`"

        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_author(name="ID: {}".format(template.id))
        embed.description = (
            "Title: `{}`\n"
            "Color: `{}`\n"
            "Binding: `{}`\n"
            "Message: {}".format(
                template.title,
                template.color,
                len(await template.reactionroles),
                jump_message,
            )
        )
        embed.set_footer(text="Status: {}".format(template.status))

        await ctx.send(embed=embed)

    @rrmanager.command(name="status")
    async def rrmanager_status(self, ctx, template_id):
        """Change a template status. On or off."""

        pass

    @rrmanager.command(name="title")
    async def rrmanager_title(self, ctx, template_id, *, title):
        """Template title update."""

        await models.Templates.get(id=template_id, guild_id=ctx.guild.id).update(
            title=title,
        )
        await ctx.send("Title updated.")

    @rrmanager.command(name="color")
    async def rrmanager_color(self, ctx, template_id, color):
        """Template color update. It accepts in 0xff00ff format."""

        await models.Templates.get(id=template_id, guild_id=ctx.guild.id).update(
            color=self.bot.color if color.lower() == "default" else int(color, 16),
        )
        await ctx.send("Color updated.")

    @rrmanager.command(name="add")
    async def rrmanager_add(self, ctx, template_id, emoji, role: discord.Role):
        """Add reaction role binding to template."""

        template = await models.Templates.get(id=template_id, guild_id=ctx.guild.id)

        # TODO: Skip if there are more than 20 binding
        # TODO: Skip the same binding if it already exists

        await models.ReactionRoles.create(
            emoji=emoji,
            role_id=role.id,
            template=template,
        )
        await ctx.send("Emoji and bindig role added.")

    @rrmanager.command(name="remove")
    @commands.has_permissions(manage_messages=True)
    async def rrmanager_remove(self, ctx, template_id, emoji):
        """Remove reaction role binding to template."""

        template = await models.Templates.get(id=template_id, guild_id=ctx.guild.id)
        await models.ReactionRoles.get(emoji=emoji, template=template).delete()
        await ctx.send("Emoji and binding role removed.")

    async def rr_embed(self, ctx, embed, template):
        description = []
        embed.set_author(name=template.title)

        async for r in template.reactionroles:
            description.append(
                "{} : {}".format(
                    r.emoji,
                    ctx.guild.get_role(r.role_id).mention,
                )
            )

        embed.description = "\n".join(description)

    @rrmanager.command(name="show")
    async def rrmanager_show(self, ctx, template_id):
        """Show reaction role template message for test."""

        template = await models.Templates.get(id=template_id, guild_id=ctx.guild.id)

        embed = discord.Embed(color=template.color)
        await self.rr_embed(ctx, embed, template)

        await ctx.send(embed=embed)

    @rrmanager.command(name="send")
    async def rrmanager_send(self, ctx, template_id, channel: discord.TextChannel):
        """Send reaction role template message to channel."""

        template = await models.Templates.get(id=template_id, guild_id=ctx.guild.id)

        embed = discord.Embed(color=template.color)
        await self.rr_embed(ctx, embed, template)

        message = await channel.send(embed=embed)
        info_message = await ctx.send("Sending...")

        template.channel_id = channel.id
        template.message_id = message.id
        await template.save()

        async for r in template.reactionroles:
            await message.add_reaction(r.emoji)

        await info_message.edit(content="{} Done.".format(info_message.content))

    @rrmanager.command(name="update")
    async def rrmanager_update(self, ctx, template_id):
        """Update reaction role template message."""

        template = await models.Templates.get(id=template_id, guild_id=ctx.guild.id)

        channel = self.bot.get_channel(template.channel_id)
        message = await channel.fetch_message(template.message_id)
        info_message = await ctx.send("Updating...")

        embed = discord.Embed(color=template.color)
        await self.rr_embed(ctx, embed, template)

        for reaction in message.reactions:
            await message.clear_reaction(reaction)

        await message.edit(embed=embed)

        async for r in template.reactionroles:
            await message.add_reaction(r.emoji)

        await info_message.edit(content="{} Done.".format(info_message.content))

    @rrmanager.command(name="kill")
    async def rrmanager_kill(self, ctx, *template_ids: commands.clean_content):
        """Kill template on the server."""

        # TODO: Get template message and delete.

        for template_id in template_ids:
            await models.Templates.get(id=template_id, guild_id=ctx.guild.id).delete()

        await ctx.send("Template(s) killed.")
