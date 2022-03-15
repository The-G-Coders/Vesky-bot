from time import time as t
from datetime import datetime


def epoch():
    """Returns the epoch plus one hour"""
    return round(t()) + 3600


def datetime_to_epoch(date: datetime):
    """Returns the epoch from the datetime object plus one hour"""
    return round(date.timestamp()) + 3600
