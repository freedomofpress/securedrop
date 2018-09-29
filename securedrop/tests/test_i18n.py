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
import os
import re

from flask import request, session, render_template_string, render_template
from flask_babel import gettext
from werkzeug.datastructures import Headers

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
import i18n
import i18n_tool
import journalist_app as journalist_app_module
import pytest
import source_app

from sh import sed, pybabel


def verify_i18n(app):
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

    # https://github.com/freedomofpress/securedrop/issues/2379
    headers = Headers([('Accept-Language',
                        'en-US;q=0.6,fr_FR;q=0.4,nb_NO;q=0.2')])
    with app.test_request_context(headers=headers):
        assert not hasattr(request, 'babel_locale')
        assert not_translated == gettext(not_translated)

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
        page = c.get('/login')
        assert session.get('locale') is None
        assert not_translated == gettext(not_translated)
        assert '?l=fr_FR' in page.data
        assert '?l=en_US' not in page.data

        page = c.get('/login?l=fr_FR',
                     headers=Headers([('Accept-Language', 'en_US')]))
        assert session.get('locale') == 'fr_FR'
        assert translated_fr == gettext(not_translated)
        assert '?l=fr_FR' not in page.data
        assert '?l=en_US' in page.data

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
        assert '?l=fr_FR' in locales
        assert '?l=en_US' not in locales
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


def test_get_supported_locales():
    locales = ['en_US', 'fr_FR']
    assert ['en_US'] == i18n._get_supported_locales(
        locales, None, None, None)
    locales = ['en_US', 'fr_FR']
    supported = ['en_US', 'not_found']
    with pytest.raises(i18n.LocaleNotFound) as excinfo:
        i18n._get_supported_locales(locales, supported, None, None)
    assert "contains ['not_found']" in str(excinfo.value)
    supported = ['fr_FR']
    locale = 'not_found'
    with pytest.raises(i18n.LocaleNotFound) as excinfo:
        i18n._get_supported_locales(locales, supported, locale, None)
    assert "DEFAULT_LOCALE 'not_found'" in str(excinfo.value)


# Grab the journalist_app fixture to trigger creation of resources
def test_i18n(journalist_app, config):
    # Then delete it because using it won't test what we want
    del journalist_app

    sources = [
        'tests/i18n/code.py',
        'tests/i18n/template.html',
    ]

    i18n_tool.I18NTool().main([
        '--verbose',
        'translate-messages',
        '--mapping', 'tests/i18n/babel.cfg',
        '--translations-dir', config.TEMP_DIR,
        '--sources', ",".join(sources),
        '--extract-update',
    ])

    pot = os.path.join(config.TEMP_DIR, 'messages.pot')
    pybabel('init', '-i', pot, '-d', config.TEMP_DIR, '-l', 'en_US')

    for (l, s) in (('fr_FR', 'code bonjour'),
                   ('zh_Hans_CN', 'code chinese'),
                   ('ar', 'code arabic'),
                   ('nb_NO', 'code norwegian'),
                   ('es_ES', 'code spanish')):
        pybabel('init', '-i', pot, '-d', config.TEMP_DIR, '-l', l)
        po = os.path.join(config.TEMP_DIR, l, 'LC_MESSAGES/messages.po')
        sed('-i', '-e',
            '/code hello i18n/,+1s/msgstr ""/msgstr "{}"/'.format(s),
            po)

    i18n_tool.I18NTool().main([
        '--verbose',
        'translate-messages',
        '--translations-dir', config.TEMP_DIR,
        '--compile',
    ])

    config.SUPPORTED_LOCALES = [
        'en_US', 'fr_FR', 'zh_Hans_CN', 'ar', 'nb_NO']
    config.TRANSLATION_DIRS = config.TEMP_DIR

    # Use our config (and not an app fixture) because the i18n module
    # grabs values at init time and we can't inject them later.
    for app in (journalist_app_module.create_app(config),
                source_app.create_app(config)):
        assert i18n.LOCALES == config.SUPPORTED_LOCALES
        verify_i18n(app)


def test_verify_default_locale_en_us_if_not_defined_in_config(config):
    class Config:
        def __getattr__(self, name):
            if name == 'DEFAULT_LOCALE':
                raise AttributeError()
            return getattr(config, name)
    not_translated = 'code hello i18n'
    with source_app.create_app(Config()).test_client() as c:
        c.get('/')
        assert not_translated == gettext(not_translated)


def test_locale_to_rfc_5646():
    assert i18n.locale_to_rfc_5646('en') == 'en'
    assert i18n.locale_to_rfc_5646('en-US') == 'en'
    assert i18n.locale_to_rfc_5646('en_US') == 'en'
    assert i18n.locale_to_rfc_5646('en-us') == 'en'
    assert i18n.locale_to_rfc_5646('zh-hant') == 'zh-Hant'


# Grab the journalist_app fixture to trigger creation of resources
def test_html_en_lang_correct(journalist_app, config):
    # Then delete it because using it won't test what we want
    del journalist_app

    app = journalist_app_module.create_app(config).test_client()
    resp = app.get('/', follow_redirects=True)
    html = resp.data.decode('utf-8')
    assert re.compile('<html .*lang="en".*>').search(html), html

    app = source_app.create_app(config).test_client()
    resp = app.get('/', follow_redirects=True)
    html = resp.data.decode('utf-8')
    assert re.compile('<html .*lang="en".*>').search(html), html

    # check '/generate' too because '/' uses a different template
    resp = app.get('/generate', follow_redirects=True)
    html = resp.data.decode('utf-8')
    assert re.compile('<html .*lang="en".*>').search(html), html


# Grab the journalist_app fixture to trigger creation of resources
def test_html_fr_lang_correct(journalist_app, config):
    """Check that when the locale is fr_FR the lang property is correct"""

    # Then delete it because using it won't test what we want
    del journalist_app

    config.SUPPORTED_LOCALES = ['fr_FR', 'en_US']
    app = journalist_app_module.create_app(config).test_client()
    resp = app.get('/?l=fr_FR', follow_redirects=True)
    html = resp.data.decode('utf-8')
    assert re.compile('<html .*lang="fr".*>').search(html), html

    app = source_app.create_app(config).test_client()
    resp = app.get('/?l=fr_FR', follow_redirects=True)
    html = resp.data.decode('utf-8')
    assert re.compile('<html .*lang="fr".*>').search(html), html

    # check '/generate' too because '/' uses a different template
    resp = app.get('/generate?l=fr_FR', follow_redirects=True)
    html = resp.data.decode('utf-8')
    assert re.compile('<html .*lang="fr".*>').search(html), html
