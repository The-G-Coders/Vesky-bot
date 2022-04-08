import discord
from textwrap import wrap
from time import time as t
from datetime import datetime
from os import getenv as env
from dotenv import load_dotenv as load

REQUIRED_ENV = ['TOKEN', 'DATABASE_URL', 'DATABASE_NAME', 'SHUTDOWN_PASSWORD', 'DEBUG_GUILD_ID', 'POLL_CHANNEL_ID', 'ANNOUNCEMENTS_CHANNEL_ID', 'BOT_CATEGORY_ID', 'EVENTS', 'SLOWMODE', 'POLLS', "UTILS"]


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
    """Returns the epoch based on the current timezone"""
    return round(t()) + 3600 * hours_from_utc()


def datetime_to_epoch(date: datetime, hours, minutes, seconds=0):
    difference = hours * 3600 + minutes * 60 + seconds - date.timestamp() % 86400
    return round(date.timestamp() + difference)


def is_7210_secs(seconds: int):
    return seconds % 86400 == 7210


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
    return to_capitalize[0].upper() + to_capitalize[1:]


def sorted_event_list(event_list: list, key: str = 'time'):
    """
    Sorts an event list by dates
    :param event_list: the event list to sort
    :param key: the key of the event field
    :return: the sorted event list
    """
    sorted_list = []
    for i in range(len(event_list)):
        min_data = Infinity()
        min_index = 0
        for index, data in enumerate(event_list):
            if data[key] <= min_data:
                min_data = data[key]
                min_index = index

        sorted_list.append(event_list[min_index])
        del event_list[min_index]
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


def init_env():
    """
    Loads the environment variables based on the env_file passed
    """

    def all_env_loaded():
        for env_var in REQUIRED_ENV:
            if env(env_var) is None:
                return False
        return True

    env_file = env('ENV_FILE')

    if env_file is not None:
        load(dotenv_path=env_file)
        print(f'Loaded .env file at "{env_file}"')
    if not all_env_loaded():
        print('The required environment variables are not loaded.')
        print('You can find the required variables at https://github.com/The-G-Coders/Vesky-bot/blob/master/README.md')
        print('Exiting...')
        exit(1)
    else:
        print('Environment variables loaded correctly.')


def intents():
    temp = discord.Intents.default()
    temp.members = True
    return temp
