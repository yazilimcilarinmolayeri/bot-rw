import json

from tortoise.models import Model
from tortoise import Tortoise, fields


async def database_init():
    await Tortoise.init(
        db_url="sqlite://database.sqlite3",
        modules={"models": ["utils.models"]},
    )
    await Tortoise.generate_schemas()


class LevelStat(Model):
    uuid = fields.UUIDField(pk=True)

    guild_id = fields.IntField()
    member_id = fields.IntField()

    level = fields.IntField(default=0)
    xp = fields.IntField(default=0)

    class Meta:
        table = "LevelStat"


class ReactionRoleTemplate(Model):
    uuid = fields.UUIDField(pk=True)
    status = fields.BooleanField(default=True)

    guild_id = fields.IntField()
    channel_id = fields.IntField(null=True)
    message_id = fields.IntField(null=True)

    embed_title = fields.CharField(default="Title", max_length=256)
    embed_color = fields.SmallIntField(default=3092790)
    bindings = fields.JSONField(
        default={},
        encoder=lambda x: json.dumps(x, ensure_ascii=False),
    )

    class Meta:
        table = "ReactionRoleTemplate"
