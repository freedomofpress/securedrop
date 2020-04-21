# -*- coding: utf-8 -*-

import random
import string

from datetime import datetime


def random_bool():
    return bool(random.getrandbits(1))


def bool_or_none():
    return random.choice([None, True, False])


def random_bytes(min, max, nullable):
    if nullable and random_bool():
        return None
    else:
        # python2 just wants strings, fix this in python3
        return random_chars(random.randint(min, max))


def random_name():
    len = random.randint(1, 100)
    return random_chars(len)


def random_username():
    len = random.randint(3, 64)
    return random_chars(len)


def random_chars(len, chars=string.printable):
    return ''.join([random.choice(chars) for _ in range(len)])


def random_ascii_chars(len, chars=string.ascii_lowercase):
    return ''.join([random.choice(chars) for _ in range(len)])


def random_datetime(nullable):
    if nullable and random_bool():
        return None
    else:
        return datetime(
            year=random.randint(1, 9999),
            month=random.randint(1, 12),
            day=random.randint(1, 28),
            hour=random.randint(0, 23),
            minute=random.randint(0, 59),
            second=random.randint(0, 59),
            microsecond=random.randint(0, 1000),
        )
