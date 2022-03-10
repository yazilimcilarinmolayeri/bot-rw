# -*- coding: utf-8 -*-

from tortoise.models import Model
from tortoise import Tortoise, fields, run_async


class EmojiUsageStat(Model):
    guild_id = fields.IntField()
    user_id = fields.IntField()
    emoji_id = fields.IntField()
    amount = fields.SmallIntField()
    last_usage = fields.DatetimeField()

    class Meta:
        table = "EmojiUsageStat"

    def __str__(self):
        return self.name

    @classmethod
    async def values_list(cls, pk):
        _ = await cls.get(pk=pk).values_list()

        try:
            return _[0]
        except IndexError:
            return []


class Feed(Model):
    feed_id = fields.CharField(pk=True, max_length=8)
    guild_id = fields.IntField()
    channel_id = fields.IntField()
    feed_url = fields.TextField()
    last_entry_url = fields.TextField()
    last_entry = fields.DatetimeField()

    class Meta:
        table = "Feed"

    def __str__(self):
        return self.name


class Profile(Model):
    user_id = fields.IntField(pk=True)
    operation_system = fields.CharField(max_length=255)
    desktop_environment = fields.CharField(max_length=255)
    desktop_themes = fields.CharField(max_length=255)
    web_browser = fields.CharField(max_length=255)
    code_editors = fields.CharField(max_length=255)
    terminal_software = fields.CharField(max_length=255)
    shell_software = fields.CharField(max_length=255)
    screenshot_url = fields.CharField(max_length=255)

    class Meta:
        table = "Profile"

    def __str__(self):
        return self.name

    @classmethod
    async def values_list(cls, pk):
        _ = await cls.get(pk=pk).values_list()

        try:
            return _[0]
        except IndexError:
            return []


class Templates(Model):
    id = fields.CharField(pk=True, max_length=8)
    guild_id = fields.IntField()
    channel_id = fields.IntField(null=True)
    message_id = fields.IntField(null=True)
    title = fields.CharField(default="Template Title", max_length=256)
    color = fields.SmallIntField(default=3092790)
    status = fields.BooleanField(default=True)

    reactionroles: fields.ReverseRelation["ReactionRoles"]

    class Meta:
        table = "Templates"

    def __str__(self):
        return self.name


class ReactionRoles(Model):
    emoji = fields.CharField(max_length=100)
    role_id = fields.IntField()

    template: fields.ForeignKeyRelation[Templates] = fields.ForeignKeyField(
        "models.Templates", related_name="reactionroles"
    )

    class Meta:
        table = "ReactionRoles"

    def __str__(self):
        return self.name


async def init():
    await Tortoise.init(
        db_url="sqlite://bot.sqlite3",
        modules={"models": ["utils.models"]},
    )
    await Tortoise.generate_schemas()
