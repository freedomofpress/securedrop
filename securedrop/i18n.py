#
# SecureDrop whistleblower submission system
# Copyright (C) 2017 Loic Dachary <loic@dachary.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from flask import Flask
from flask import request, session
from flask_babel import Babel
from babel import core

import collections
import os
import re

from typing import List

from typing import Dict

from sdconfig import SDConfig

LOCALE_SPLIT = re.compile('(-|_)')
LOCALES = ['en_US']
babel = None


class LocaleNotFound(Exception):

    """Raised when the desired locale is not in the translations directory"""


def setup_app(config: SDConfig, app: Flask) -> None:
    global LOCALES
    global babel

    # `babel.translation_directories` is a nightmare
    # We need to set this manually via an absolute path
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = str(config.TRANSLATION_DIRS.absolute())

    babel = Babel(app)
    if len(list(babel.translation_directories)) != 1:
        raise AssertionError(
            'Expected exactly one translation directory but got {}.'
            .format(babel.translation_directories))

    translation_directories = next(babel.translation_directories)
    for dirname in os.listdir(translation_directories):
        if dirname != 'messages.pot':
            LOCALES.append(dirname)

    LOCALES = _get_supported_locales(
        LOCALES,
        config.SUPPORTED_LOCALES,
        config.DEFAULT_LOCALE,
        translation_directories)

    babel.localeselector(lambda: get_locale(config))


def get_locale(config: SDConfig) -> str:
    """
    Get the locale as follows, by order of precedence:
    - l request argument or session['locale']
    - browser suggested locale, from the Accept-Languages header
    - config.DEFAULT_LOCALE
    - 'en_US'
    """
    accept_languages = []
    for l in list(request.accept_languages.values()):
        if '-' in l:
            sep = '-'
        else:
            sep = '_'
        try:
            accept_languages.append(str(core.Locale.parse(l, sep)))
        except Exception:
            pass
    if 'l' in request.args:
        if len(request.args['l']) == 0:
            if 'locale' in session:
                del session['locale']
            locale = core.negotiate_locale(accept_languages, LOCALES)
        else:
            locale = core.negotiate_locale([request.args['l']], LOCALES)
            session['locale'] = locale
    else:
        if 'locale' in session:
            locale = session['locale']
        else:
            locale = core.negotiate_locale(accept_languages, LOCALES)

    if locale:
        return locale
    else:
        return config.DEFAULT_LOCALE


def get_text_direction(locale: str) -> str:
    return core.Locale.parse(locale).text_direction


def _get_supported_locales(locales: List[str], supported: List[str], default_locale: str,
                           translation_directories: str) -> List[str]:
    """Sanity checks on locales and supported locales from config.py.
    Return the list of supported locales.
    """

    if not supported:
        return [default_locale or 'en_US']
    unsupported = set(supported) - set(locales)
    if unsupported:
        raise LocaleNotFound(
            "config.py SUPPORTED_LOCALES contains {} which is not among the "
            "locales found in the {} directory: {}".format(
                list(unsupported),
                translation_directories,
                locales))
    if default_locale and default_locale not in supported:
        raise LocaleNotFound("config.py SUPPORTED_LOCALES contains {} "
                             "which does not include "
                             "the value of DEFAULT_LOCALE '{}'".format(
                                 supported, default_locale))

    return list(supported)


NAME_OVERRIDES = {
    'nb_NO':  'norsk',
}


def get_locale2name() -> Dict[str, str]:
    locale2name = collections.OrderedDict()
    for l in LOCALES:
        if l in NAME_OVERRIDES:
            locale2name[l] = NAME_OVERRIDES[l]
        else:
            locale = core.Locale.parse(l)
            locale2name[l] = locale.languages[locale.language]
    return locale2name


def locale_to_rfc_5646(locale: str) -> str:
    lower = locale.lower()
    if 'hant' in lower:
        return 'zh-Hant'
    elif 'hans' in lower:
        return 'zh-Hans'
    else:
        return LOCALE_SPLIT.split(locale)[0]


def get_language(config: SDConfig) -> str:
    return get_locale(config).split('_')[0]
