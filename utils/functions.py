# -*- coding: utf-8 -*-

import re
import csv
import string
import random
import discord
import mimetypes
from collections import Counter


def list_to_matrix(l, col=10):
    return [l[i : i + col] for i in range(0, len(l), col)]


def is_url_image(url):
    mimetype, encoding = mimetypes.guess_type(url)

    return mimetype and mimetype.startswith("image")


def custom_emoji_counter(guild, message):
    custom_emoji_regex = (
        r"<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>"
    )

    custom_emojis = Counter(
        [
            discord.utils.get(guild.emojis, id=emoji_id)
            for emoji_id in [
                int(emoji[2])
                for emoji in re.findall(custom_emoji_regex, message.content)
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


def random_id(length=8):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
