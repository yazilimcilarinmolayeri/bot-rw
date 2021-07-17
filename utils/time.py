# -*- coding: utf-8 -*-

import arrow


def day_month_year(value):
    return (value.day, value.month, value.year)


def humanize(dt, l="tr", od=False, g="auto"):
    return arrow.get(dt).humanize(locale=l, only_distance=od, granularity=g)


def format_dt(dt, style=None):
    if style is None:
        return "<t:{}>".format(int(dt.timestamp()))

    return "<t:{}:{}>".format(int(dt.timestamp()), style)
