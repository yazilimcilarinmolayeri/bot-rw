# -*- coding: utf-8 -*-

import datetime as dt


timezone = dt.timezone.utc


def day_month_year(value):
    """
    Args:
        value (datetime.datetime): A datetime.

    Returns:
        tuple: Day, month and year information.
    """

    return (value.day, value.month, value.year)


def days_ago(value, label=True):
    """
    Args:
        value (datetime.datetime): A datetime.
        label (bool):

    Returns:
        int: Days information.
    """

    return (dt.datetime.now(timezone) - value).days
