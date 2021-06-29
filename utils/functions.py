# -*- coding: utf-8 -*-

import re
import csv
import discord
import mimetypes
from collections import Counter


def list_to_matrix(l, col=10):
    return [l[i : i + col] for i in range(0, len(l), col)]


def is_url_image(url):
    mimetype, encoding = mimetypes.guess_type(url)

    return mimetype and mimetype.startswith("image")


def custom_emoji_counter(guild, message):
    custom_emojis = Counter(
        [
            discord.utils.get(guild.emojis, id=e)
            for e in [
                int(e.split(":")[2].replace(">", ""))
                for e in re.findall(r"<:\w*:\d*>", message.content)
            ]
        ]
    )

    if None in custom_emojis:
        del custom_emojis[None]

    return custom_emojis


def dist():
    release_data = {}

    with open("/etc/os-release") as f:
        reader = csv.reader(f, delimiter="=")

        for row in reader:
            if row:
                release_data[row[0]] = row[1]

    return release_data
