# -*- coding: utf-8 -*-

from os import environ as env
from discord import Status, ActivityType


PREFIX = ["."]
TOKEN = "" or env.get("TOKEN")
STATUS_TYPE = Status.idle
ACTIVITY_TYPE = ActivityType.watching

# =============================================================================

DEFAULT_GUILD_ID = 418887354699350028  # YMY
