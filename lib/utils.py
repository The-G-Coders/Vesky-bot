from time import time as t
from datetime import datetime

characters = r'!@#$%^&*()-_=+[]{};:"/?.>,<|`~ '


def epoch():
    """Returns the epoch plus one hour"""
    return round(t()) + 3600


def datetime_to_epoch(date: datetime):
    """
    Returns the epoch from the datetime object plus one hour
    :param date: a datetime object
    :return the epoch
    """
    return round(date.timestamp()) + 3600


def seconds_to_time(seconds: int):
    """
    Converts seconds to a readable time of the day
    :param seconds: the seconds to convert
    :return the converted time
    """
    secs = seconds % 86400
    hours = secs // 3600
    minutes = (secs - hours * 3600) // 60
    return f'{hours}:{minutes if minutes > 9 else f"0{minutes}"}'


def capitalize_first_letter(to_capitalize: str):
    """
    Makes the first character in a string a capital
    :param to_capitalize: the string to capitalize
    :return: the capitalized string
    """
    new = ''
    index = 0
    for v in to_capitalize:
        if index == 0 and v not in characters:
            new += v.upper()
            index = 1
        else:
            new += v

    return new
