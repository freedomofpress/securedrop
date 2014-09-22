# -*- coding: utf-8 -*-
from datetime import datetime
from jinja2 import Markup, escape


def datetimeformat(dt, fmt=None, relative=False):
    """Template filter for readable formatting of datetime.datetime"""
    fmt = fmt or '%b %d, %Y %I:%M %p'
    if relative:
        time_difference = _relative_timestamp(dt)
        if time_difference:
            return '{} ago'.format(time_difference)
    return dt.strftime(fmt)


def _relative_timestamp(dt):
    """"
    Format a human readable relative time for timestamps up to 30 days old
    """
    delta = datetime.now() - dt
    diff = (delta.microseconds + (delta.seconds + delta.days * 24 * 3600) * 1e6) / 1e6
    if diff < 45:
        return '{} second{}'.format(int(diff), 's' if int(diff) == 1 else '')
    elif diff < 90:
        return 'a minute'
    elif diff < 2700:
        return '{} minutes'.format(int(max(diff / 60, 2)))
    elif diff < 5400:
        return 'an hour'
    elif diff < 79200:
        return '{} hours'.format(int(max(diff / 3600, 2)))
    elif diff < 129600:
        return 'a day'
    elif diff < 2592000:
        return '{} days'.format(int(max(diff / 86400, 2)))
    else:
        return None


def nl2br(context, value):
    formatted = u'<br>\n'.join(escape(value).split('\n'))
    if context.autoescape:
        formatted = Markup(formatted)
    return formatted
