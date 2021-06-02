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


async def init():
    await Tortoise.init(
        db_url="sqlite://ymybot-rw-db.sqlite3",
        modules={"models": ["utils.models"]},
    )
    await Tortoise.generate_schemas()
