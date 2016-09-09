# -*- coding: utf-8 -*-
from datetime import datetime
from jinja2 import Markup, escape
from flask.ext.babel import gettext


def rel_datetimeformat(dt, fmt=None, relative=False):
    """Template filter for readable formatting of datetime.datetime"""
    fmt = fmt or '%b %d, %Y %I:%M %p'
    if relative:
        return _relative_timestamp(dt)
    return dt.strftime(fmt)


def _relative_timestamp(dt):
    """"
    Format to a human readable relative time
    """
    delta = datetime.utcnow() - dt
    diff = (
        delta.microseconds + (delta.seconds + delta.days * 24 * 3600) * 1e6) / 1e6
    if diff < 45:
        return gettext('{seconds} seconds ago').format(seconds=diff)
    elif diff < 90:
        return gettext('a minute ago')
    elif diff < 2700:
        return gettext('{minutes} minutes ago').format(minutes=int(max(diff / 60, 2)))
    elif diff < 5400:
        return gettext('an hour ago')
    elif diff < 79200:
        return gettext('{hours} hours ago').format(hours=int(max(diff / 3600, 2)))
    elif diff < 129600:
        return gettext('a day ago')
    else:
        return gettext('{days} days ago').format(days=int(max(diff / 86400, 2)))


def nl2br(context, value):
    formatted = u'<br>\n'.join(escape(value).split('\n'))
    if context.autoescape:
        formatted = Markup(formatted)
    return formatted
