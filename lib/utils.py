from textwrap import wrap
from time import time as t
from datetime import datetime

characters = r'!@#$%^&*()-_=+[]{};:"/?.>,<|`~ '


class Infinity:

    def __init__(self) -> None:
        pass

    def __eq__(self, number):
        return False

    __ne__ = __eq__

    __lt__ = __eq__

    __le__ = __eq__

    def __ge__(self, number):
        return True

    __gt__ = __ge__

    def __add__(self, number):
        return Infinity()

    __radd__ = __add__


def hours_from_utc():
    """
    Returns the difference between utc and the current timezone
    :return:
    """
    utc_offset_min = int(round((datetime.now() - datetime.utcnow()).total_seconds())) / 60
    utc_offset_h = utc_offset_min / 60
    assert (utc_offset_min == utc_offset_h * 60)
    return int(utc_offset_h)


def epoch():
    """Returns the epoch plus one hour"""
    return round(t()) + 3600 * hours_from_utc()


def datetime_to_epoch(date: datetime):
    """
    Returns the epoch from the datetime object plus one hour
    :param date: a datetime object
    :return the epoch
    """
    return round(date.timestamp() + 3600 * hours_from_utc())


def is_10_secs(seconds: int):
    return seconds % 86400 == 10


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


def sorted_event_dict(dictionary: dict, key: str = 'time'):
    """
    Sorts an event dictionary by dates
    :param dictionary: the dictionary to sort
    :param key: the key of the event field
    :return: the sorted dict
    """
    sorted_list = []
    processed = []
    for i in range(len(dictionary)):
        min_name = ''
        min_data = Infinity()
        for name, data in dictionary.items():
            if name not in processed and data[key] <= min_data:
                min_name = name
                min_data = data[key]

        sorted_list.append((min_name, dictionary[min_name]))
        processed.append(min_name)

    return sorted_list


def wrap_text(text: str, count: int):
    """
    Inserts line brakes to a string after a specified number of characters
    :param text: the text to process
    :param count: the number of characters per line
    :return: the processed string
    """
    split = wrap(text, count)
    return '\n'.join(split)
