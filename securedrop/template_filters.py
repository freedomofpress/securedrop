# -*- coding: utf-8 -*-
from flask_babel import gettext, ngettext, get_locale
from babel import units
from datetime import datetime
from jinja2 import Markup, escape
import math


def datetimeformat(dt, fmt=None, relative=False):
    """Template filter for readable formatting of datetime.datetime"""
    fmt = fmt or '%b %d, %Y %I:%M %p'
    if relative:
        time_difference = _relative_timestamp(dt)
        if time_difference:
            return gettext('{time} ago').format(time=time_difference)
    return dt.strftime(fmt)


def _relative_timestamp(dt):
    """"
    Format a human readable relative time for timestamps up to 30 days old
    """
    delta = datetime.utcnow() - dt
    diff = (
        delta.microseconds + (delta.seconds +
                              delta.days * 24 * 3600) * 1e6) / 1e6
    if diff < 45:
        return ngettext('{n} second', '{n} seconds', int(diff)).format(
            n=int(diff))
    elif diff < 90:
        return gettext('a minute')
    elif diff < 2700:
        return gettext('{n} minutes').format(n=int(max(diff / 60, 2)))
    elif diff < 5400:
        return gettext('an hour')
    elif diff < 79200:
        return gettext('{n} hours').format(n=int(max(diff / 3600, 2)))
    elif diff < 129600:
        return gettext('a day')
    elif diff < 2592000:
        return gettext('{n} days').format(n=int(max(diff / 86400, 2)))
    else:
        return None


def nl2br(context, value):
    formatted = u'<br>\n'.join(escape(value).split('\n'))
    if context.autoescape:
        formatted = Markup(formatted)
    return formatted


def filesizeformat(value):
    prefixes = [
        'digital-kilobyte',
        'digital-megabyte',
        'digital-gigabyte',
        'digital-terabyte',
    ]
    locale = get_locale()
    base = 1024
    #
    # we are using the long length because the short length has no
    # plural variant and it reads like a bug instead of something
    # on purpose
    #
    if value < base:
        return units.format_unit(value, "byte", locale=locale, length="long")
    else:
        i = min(int(math.log(value, base)), len(prefixes)) - 1
        prefix = prefixes[i]
        bytes = float(value) / base ** (i + 1)
        return units.format_unit(bytes, prefix, locale=locale, length="short")
