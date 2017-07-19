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
from flask import request, session
from flask_babel import Babel
from babel import core

import collections
import config
import os

LOCALES = set(['en_US'])


def setup_app(app):
    babel = Babel(app)
    assert len(list(babel.translation_directories)) == 1
    for dirname in os.listdir(next(babel.translation_directories)):
        if dirname != 'messages.pot':
            LOCALES.add(dirname)

    babel.localeselector(get_locale)


def get_locale():
    """
    Get the locale as follows, by order of precedence:
    - l request argument or session['locale']
    - browser suggested locale, from the Accept-Languages header
    - config.DEFAULT_LOCALE
    - 'en_US'
    """
    locale = None
    accept_languages = set()
    for l in request.accept_languages.values():
        if '-' in l:
            sep = '-'
        else:
            sep = '_'
        try:
            accept_languages.add(str(core.Locale.parse(l, sep)))
        except:
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
        return getattr(config, 'DEFAULT_LOCALE', 'en_US')


def get_locale2name():
    locale2name = collections.OrderedDict()
    for l in sorted(LOCALES):
        locale = core.Locale.parse(l)
        locale2name[l] = locale.languages[locale.language]
    return locale2name
