from time import time as t
from datetime import datetime

characters = r'!@#$%^&*()-_=+[]{};:"/?.>,<|`~ '

class Infinity:

    def __init__(self) -> None:
        pass
    
    def __eq__(self, cislo):
        return False
    
    __ne__=__eq__

    __lt__=__eq__

    __le__=__eq__

    __ge__=__eq__

    def __gt__(self, cislo):
        return True
    
    def __add__(self, cislo):
        return Infinity()
    
    __radd__=__add__

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


def sorted_event_dict(dict: dict, key: str = 'time'):

    sorted_list = []
    spracovane=[]
    for i in len(dict):
        min_name=''
        min_data=Infinity()
        for name, data in dict.items():
            if name not in spracovane and data[key] <= min_data:
                min_name = name
                min_data = data[key]

        sorted_list.append( (min_name, dict[min_name]) )
        spracovane.append(min_name)

    return sorted_list
