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
import source


class TestI18N(object):

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
            assert session.get('locale') == None
            assert not_translated == gettext(not_translated)

        with app.test_request_context():
            assert '' == render_template('locales.html')

        with app.test_client() as c:
            c.get('/')
            locales = render_template('locales.html')
            assert 'fr_FR' in locales
            assert 'en_US' not in locales

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
        }
        args = argparse.Namespace(**kwargs)
        manage.setup_verbosity(args)
        manage.translate(args)

        manage.sh("""
        pybabel init -i {d}/messages.pot -d {d} -l en_US
        pybabel init -i {d}/messages.pot -d {d} -l fr_FR
        sed -i -e '/code hello i18n/,+1s/msgstr ""/msgstr "code bonjour"/' \
              {d}/fr_FR/LC_MESSAGES/messages.po
        pybabel init -i {d}/messages.pot -d {d} -l zh_Hans_CN
        sed -i -e '/code hello i18n/,+1s/msgstr ""/msgstr "code chinese"/' \
              {d}/zh_Hans_CN/LC_MESSAGES/messages.po
        """.format(d=config.TEMP_DIR))

        manage.translate(args)

        for app in (journalist.app, source.app):
            app.config['BABEL_TRANSLATION_DIRECTORIES'] = config.TEMP_DIR
            i18n.setup_app(app)
            self.verify_i18n(app)

    @classmethod
    def teardown_class(cls):
        reload(journalist)
        reload(source)
        reload(config)
        reload(i18n)
