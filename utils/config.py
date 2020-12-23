# -*- coding: utf-8 -*-

from os import environ as env
from discord import Status, ActivityType
from socialscan.util import Platforms as p


PREFIX = ["."]
TOKEN = "" or env.get("TOKEN")
STATUS_TYPE = Status.idle
ACTIVITY_TYPE = ActivityType.watching

# =============================================================================

PLATFORMS = [
    p.TWITTER, p.INSTAGRAM, p.REDDIT, p.GITHUB, p.GITLAB, p.SPOTIFY
]

# =============================================================================

DEFAULT_GUILD_ID = 418887354699350028  # YMY

MENTION_LOG_CHANNEL_ID = 687805076857028671
DM_LOG_CHANNEL_ID = 687804890860486762
