# -*- coding: utf-8 -*-
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
import argparse
import logging
import os

from flask import request, session, render_template, render_template_string
from flask_babel import gettext
from werkzeug.datastructures import Headers

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
import config
import i18n
import journalist
import manage
import pytest
import source
import version


class TestI18N(object):

    def test_get_supported_locales(self):
        locales = ['en_US', 'fr_FR']
        assert locales == i18n._get_supported_locales(locales, None, None)
        locales = ['en_US', 'fr_FR']
        supported = ['en_US', 'not_found']
        with pytest.raises(Exception) as excinfo:
            i18n._get_supported_locales(locales, supported, None)
        assert "contains ['not_found']" in str(excinfo.value)
        supported = ['fr_FR']
        locale = 'not_found'
        with pytest.raises(Exception) as excinfo:
            i18n._get_supported_locales(locales, supported, locale)
        assert "DEFAULT_LOCALE 'not_found'" in str(excinfo.value)

    def verify_i18n(self, app):
        not_translated = 'code hello i18n'
        translated_fr = 'code bonjour'

        for accepted in ('unknown', 'en_US'):
            headers = Headers([('Accept-Language', accepted)])
            with app.test_request_context(headers=headers):
                assert not hasattr(request, 'babel_locale')
                assert not_translated == gettext(not_translated)
                assert hasattr(request, 'babel_locale')
                assert render_template_string('''
                {{ gettext('code hello i18n') }}
                ''').strip() == not_translated

        for lang in ('fr_FR', 'fr', 'fr-FR'):
            headers = Headers([('Accept-Language', lang)])
            with app.test_request_context(headers=headers):
                assert not hasattr(request, 'babel_locale')
                assert translated_fr == gettext(not_translated)
                assert hasattr(request, 'babel_locale')
                assert render_template_string('''
                {{ gettext('code hello i18n') }}
                ''').strip() == translated_fr

        translated_cn = 'code chinese'

        for lang in ('zh-CN', 'zh-Hans-CN'):
            headers = Headers([('Accept-Language', lang)])
            with app.test_request_context(headers=headers):
                assert not hasattr(request, 'babel_locale')
                assert translated_cn == gettext(not_translated)
                assert hasattr(request, 'babel_locale')
                assert render_template_string('''
                {{ gettext('code hello i18n') }}
                ''').strip() == translated_cn

        translated_ar = 'code arabic'

        for lang in ('ar', 'ar-kw'):
            headers = Headers([('Accept-Language', lang)])
            with app.test_request_context(headers=headers):
                assert not hasattr(request, 'babel_locale')
                assert translated_ar == gettext(not_translated)
                assert hasattr(request, 'babel_locale')
                assert render_template_string('''
                {{ gettext('code hello i18n') }}
                ''').strip() == translated_ar

        with app.test_client() as c:
            c.get('/')
            assert session.get('locale') is None
            assert not_translated == gettext(not_translated)

            c.get('/?l=fr_FR', headers=Headers([('Accept-Language', 'en_US')]))
            assert session.get('locale') == 'fr_FR'
            assert translated_fr == gettext(not_translated)

            c.get('/', headers=Headers([('Accept-Language', 'en_US')]))
            assert session.get('locale') == 'fr_FR'
            assert translated_fr == gettext(not_translated)

            c.get('/?l=')
            assert session.get('locale') is None
            assert not_translated == gettext(not_translated)

            c.get('/?l=en_US', headers=Headers([('Accept-Language', 'fr_FR')]))
            assert session.get('locale') == 'en_US'
            assert not_translated == gettext(not_translated)

            c.get('/', headers=Headers([('Accept-Language', 'fr_FR')]))
            assert session.get('locale') == 'en_US'
            assert not_translated == gettext(not_translated)

            c.get('/?l=', headers=Headers([('Accept-Language', 'fr_FR')]))
            assert session.get('locale') is None
            assert translated_fr == gettext(not_translated)

            c.get('/')
            assert session.get('locale') is None
            assert not_translated == gettext(not_translated)

            c.get('/?l=YY_ZZ')
            assert session.get('locale') is None
            assert not_translated == gettext(not_translated)

        with app.test_request_context():
            assert '' == render_template('locales.html')

        with app.test_client() as c:
            c.get('/')
            locales = render_template('locales.html')
            assert 'fr_FR' in locales
            assert 'en_US' not in locales

            base = render_template('base.html')
            assert 'dir="ltr"' in base

        with app.test_client() as c:
            c.get('/?l=ar')
            base = render_template('base.html')
            assert 'dir="rtl"' in base

        # the canonical locale name is norsk bokmål but
        # this is overriden with just norsk by i18n.NAME_OVERRIDES
        with app.test_client() as c:
            c.get('/?l=nb_NO')
            base = render_template('base.html')
            assert 'norsk' in base
            assert 'norsk bo' not in base

    def test_i18n(self):
        sources = [
            'tests/i18n/code.py',
            'tests/i18n/template.html',
        ]
        kwargs = {
            'translations_dir': config.TEMP_DIR,
            'mapping': 'tests/i18n/babel.cfg',
            'source': sources,
            'extract_update': True,
            'compile': True,
            'verbose': logging.DEBUG,
            'version': version.__version__,
        }
        args = argparse.Namespace(**kwargs)
        manage.setup_verbosity(args)
        manage.translate_messages(args)

        manage.sh("""
        pybabel init -i {d}/messages.pot -d {d} -l en_US
        pybabel init -i {d}/messages.pot -d {d} -l fr_FR
        sed -i -e '/code hello i18n/,+1s/msgstr ""/msgstr "code bonjour"/' \
              {d}/fr_FR/LC_MESSAGES/messages.po
        pybabel init -i {d}/messages.pot -d {d} -l zh_Hans_CN
        sed -i -e '/code hello i18n/,+1s/msgstr ""/msgstr "code chinese"/' \
              {d}/zh_Hans_CN/LC_MESSAGES/messages.po
        pybabel init -i {d}/messages.pot -d {d} -l ar
        sed -i -e '/code hello i18n/,+1s/msgstr ""/msgstr "code arabic"/' \
              {d}/ar/LC_MESSAGES/messages.po
        pybabel init -i {d}/messages.pot -d {d} -l nb_NO
        sed -i -e '/code hello i18n/,+1s/msgstr ""/msgstr "code norwegian"/' \
              {d}/nb_NO/LC_MESSAGES/messages.po
        """.format(d=config.TEMP_DIR))

        manage.translate_messages(args)

        for app in (journalist.app, source.app):
            app.config['BABEL_TRANSLATION_DIRECTORIES'] = config.TEMP_DIR
            i18n.setup_app(app)
            self.verify_i18n(app)

    def test_verify_default_locale_en_us_if_not_defined_in_config(self):
        DEFAULT_LOCALE = config.DEFAULT_LOCALE
        try:
            del config.DEFAULT_LOCALE
            not_translated = 'code hello i18n'
            with source.app.test_client() as c:
                c.get('/')
                assert not_translated == gettext(not_translated)
        finally:
            config.DEFAULT_LOCALE = DEFAULT_LOCALE

    @classmethod
    def teardown_class(cls):
        reload(journalist)
        reload(source)
