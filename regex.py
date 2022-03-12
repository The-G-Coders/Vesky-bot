import re

days1_28 = '\d|1\d|2[0-8]'

days_29_30 = '29|30'

days_31 = '31'

months = '[1-9]|1[0-2]'

years = '19[7-9]\d|2\d{3}'

leap_years = '19(?:[79][26]|8[048])|2\d(?:[13579][26]|[02468][048])'

separators = '\/|\.|-'

months_with_31 = '^(?<monthsWith31>31({0})(?:[13578]|1[02])\\2(?:{1}))$'.format(separators, years)

months_with_29_or_30 = '^(?<monthsWith29or30>(?:29|30)({0})(?:[1, 3-9]|1[0-2])\\4(?:{1}))$'.format(separators, years)

months_with_28 = '^(?<monthsWith28>(?:[1-9]|1[0-9]|2[0-8])({0})(?:[1-9]|1[0-2])\\6(?:{1}))$'.format(separators, years)

month_leap = '^(?<monthLeap>29({0})2\8(?:{1}))$'.format(separators, leap_years)

clean_months_with_31 = '^31({0})(?:[13578]|1[02])\\1(?:{1})$'.format(separators, years)

clean_months_with_29_or_30 = r'^(?:29|30)({0})(?:[1, 3-9]|1[0-2])\2(?:{1})$'.format(separators, years)

clean_months_with_28 = '^(?:[1-9]|1[0-9]|2[0-8])({0})(?:[1-9]|1[0-2])\\3(?:{1})$'.format(separators, years)

clean_month_leap = '^29({0})2\\4(?:{1})$'.format(separators, leap_years)

reg_months = '{0}|{1}|{2}|{3}'.format(clean_months_with_31, clean_months_with_29_or_30, clean_months_with_28,
                                      clean_month_leap)

named_reg = '{0}|{1}|{2}|{3}'.format(months_with_31, months_with_29_or_30, months_with_28, month_leap)

DATE_PATTERN = re.compile(reg_months)


def get_separator(date: str):
    if not DATE_PATTERN.match(date):
        return None
    for string in DATE_PATTERN.findall(date)[0]:
        if string != '':
            return string
    return None


def print_reg():
    print(reg_months)


def print_named_reg():
    print(named_reg)


def generate_years(count: int, gap: int, start: int):
    dummy = start
    for i in range(count):
        print(dummy)
        dummy += gap
