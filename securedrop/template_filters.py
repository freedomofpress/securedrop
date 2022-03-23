# -*- coding: utf-8 -*-
from jinja2 import pass_eval_context
from flask_babel import gettext, get_locale
from babel import units, dates
from datetime import datetime
from markupsafe import Markup, escape
import math

from jinja2.nodes import EvalContext


def rel_datetime_format(
    dt: datetime, fmt: str = 'long',
    relative: bool = False
) -> str:
    """Template filter for readable formatting of datetime.datetime"""
    if relative:
        time = dates.format_timedelta(datetime.utcnow() - dt,
                                      locale=get_locale())
        return gettext('{time} ago').format(time=time)
    else:
        return dates.format_datetime(dt, fmt, locale=get_locale())


@pass_eval_context
def nl2br(context: EvalContext, value: str) -> str:
    formatted = '<br>\n'.join(escape(value).split('\n'))
    if context.autoescape:
        formatted = Markup(formatted)
    return formatted


def filesizeformat(value: int) -> str:
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


def html_datetime_format(dt: datetime) -> str:
    """Return a datetime string that will pass HTML validation"""
    return dates.format_datetime(dt, 'yyyy-MM-dd HH:mm:ss.SSS')
