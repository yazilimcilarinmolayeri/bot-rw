# -*- coding: utf-8 -*-

import arrow


def day_month_year(value):
    return (value.day, value.month, value.year)


def humanize(dt, locale="tr", granularity=["day"]):

    return arrow.get(dt).humanize(locale=locale, granularity=granularity)
