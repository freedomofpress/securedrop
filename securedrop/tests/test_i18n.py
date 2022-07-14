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
from pathlib import Path

import i18n
import i18n_tool
import journalist_app as journalist_app_module
import pytest
import source_app
from babel.core import Locale, UnknownLocaleError
from db import db
from flask import render_template, render_template_string, request, session
from flask_babel import gettext
from i18n import parse_locale_set
from sdconfig import FALLBACK_LOCALE, SDConfig
from sh import pybabel, sed
from werkzeug.datastructures import Headers

from .utils.env import TESTS_DIR

NEVER_LOCALE = "eo"  # Esperanto


def verify_i18n(app):
    not_translated = "code hello i18n"
    translated_fr = "code bonjour"

    for accepted in ("unknown", "en_US"):
        headers = Headers([("Accept-Language", accepted)])
        with app.test_request_context(headers=headers):
            assert not hasattr(request, "babel_locale")
            assert not_translated == gettext(not_translated)
            assert hasattr(request, "babel_locale")
            assert (
                render_template_string(
                    """
            {{ gettext('code hello i18n') }}
            """
                ).strip()
                == not_translated
            )

    for lang in ("fr", "fr-FR"):
        headers = Headers([("Accept-Language", lang)])
        with app.test_request_context(headers=headers):
            assert not hasattr(request, "babel_locale")
            assert translated_fr == gettext(not_translated)
            assert hasattr(request, "babel_locale")
            assert (
                render_template_string(
                    """
            {{ gettext('code hello i18n') }}
            """
                ).strip()
                == translated_fr
            )

    # https://github.com/freedomofpress/securedrop/issues/2379
    headers = Headers([("Accept-Language", "en-US;q=0.6,fr_FR;q=0.4,nb_NO;q=0.2")])
    with app.test_request_context(headers=headers):
        assert not hasattr(request, "babel_locale")
        assert not_translated == gettext(not_translated)

    translated_cn = "code chinese"

    for lang in ("zh-CN", "zh-Hans-CN"):
        headers = Headers([("Accept-Language", lang)])
        with app.test_request_context(headers=headers):
            assert not hasattr(request, "babel_locale")
            assert translated_cn == gettext(not_translated)
            assert hasattr(request, "babel_locale")
            assert (
                render_template_string(
                    """
            {{ gettext('code hello i18n') }}
            """
                ).strip()
                == translated_cn
            )

    translated_ar = "code arabic"

    for lang in ("ar", "ar-kw"):
        headers = Headers([("Accept-Language", lang)])
        with app.test_request_context(headers=headers):
            assert not hasattr(request, "babel_locale")
            assert translated_ar == gettext(not_translated)
            assert hasattr(request, "babel_locale")
            assert (
                render_template_string(
                    """
            {{ gettext('code hello i18n') }}
            """
                ).strip()
                == translated_ar
            )

    with app.test_client() as c:

        # a request without Accept-Language or "l" argument gets the
        # default locale
        page = c.get("/login")
        assert session.get("locale") == "en_US"
        assert not_translated == gettext(not_translated)
        assert b"?l=fr_FR" in page.data
        assert b"?l=en_US" not in page.data

        # the session locale should change when the "l" request
        # argument is present and valid
        page = c.get("/login?l=fr_FR", headers=Headers([("Accept-Language", "en_US")]))
        assert session.get("locale") == "fr_FR"
        assert translated_fr == gettext(not_translated)
        assert b"?l=fr_FR" not in page.data
        assert b"?l=en_US" in page.data

        # confirm that the chosen locale, now in the session, is used
        # despite not matching the client's Accept-Language header
        c.get("/", headers=Headers([("Accept-Language", "en_US")]))
        assert session.get("locale") == "fr_FR"
        assert translated_fr == gettext(not_translated)

        # the session locale should not change if an empty "l" request
        # argument is sent
        c.get("/?l=")
        assert session.get("locale") == "fr_FR"
        assert translated_fr == gettext(not_translated)

        # the session locale should not change if no "l" request
        # argument is sent
        c.get("/")
        assert session.get("locale") == "fr_FR"
        assert translated_fr == gettext(not_translated)

        # sending an invalid locale identifier should not change the
        # session locale
        c.get("/?l=YY_ZZ")
        assert session.get("locale") == "fr_FR"
        assert translated_fr == gettext(not_translated)

        # requesting a valid locale via the request argument "l"
        # should change the session locale
        c.get("/?l=en_US", headers=Headers([("Accept-Language", "fr_FR")]))
        assert session.get("locale") == "en_US"
        assert not_translated == gettext(not_translated)

        # again, the session locale should stick even if not included
        # in the client's Accept-Language header
        c.get("/", headers=Headers([("Accept-Language", "fr_FR")]))
        assert session.get("locale") == "en_US"
        assert not_translated == gettext(not_translated)

    with app.test_request_context():
        assert "" == render_template("locales.html")

    with app.test_client() as c:
        c.get("/")
        locales = render_template("locales.html")
        assert "?l=fr_FR" in locales
        assert "?l=en_US" not in locales

        # Test that A[lang,hreflang] attributes (if present) will validate as
        # BCP47/RFC5646 language tags from `i18n.RequestLocaleInfo.language_tag`.
        if 'lang="' in locales:
            assert 'lang="en-US"' in locales
            assert 'lang="fr-FR"' in locales
        if 'hreflang="' in locales:
            assert 'hreflang="en-US"' in locales
            assert 'hreflang="fr-FR"' in locales

        c.get("/?l=ar")
        base = render_template("base.html")
        assert 'dir="rtl"' in base


# Grab the journalist_app fixture to trigger creation of resources
def test_i18n(journalist_app, config):
    # Then delete it because using it won't test what we want
    del journalist_app

    sources = [
        os.path.join(TESTS_DIR, "i18n/code.py"),
        os.path.join(TESTS_DIR, "i18n/template.html"),
    ]

    i18n_tool.I18NTool().main(
        [
            "--verbose",
            "translate-messages",
            "--mapping",
            os.path.join(TESTS_DIR, "i18n/babel.cfg"),
            "--translations-dir",
            config.TEMP_DIR,
            "--sources",
            ",".join(sources),
            "--extract-update",
        ]
    )

    pot = os.path.join(config.TEMP_DIR, "messages.pot")
    pybabel("init", "-i", pot, "-d", config.TEMP_DIR, "-l", "en_US")

    for (l, s) in (
        ("fr_FR", "code bonjour"),
        ("zh_Hans", "code chinese"),
        ("ar", "code arabic"),
        ("nb_NO", "code norwegian"),
        ("es_ES", "code spanish"),
    ):
        pybabel("init", "-i", pot, "-d", config.TEMP_DIR, "-l", l)
        po = os.path.join(config.TEMP_DIR, l, "LC_MESSAGES/messages.po")
        sed("-i", "-e", '/code hello i18n/,+1s/msgstr ""/msgstr "{}"/'.format(s), po)

    i18n_tool.I18NTool().main(
        [
            "--verbose",
            "translate-messages",
            "--translations-dir",
            config.TEMP_DIR,
            "--compile",
        ]
    )

    fake_config = SDConfig()
    fake_config.SUPPORTED_LOCALES = ["ar", "en_US", "fr_FR", "nb_NO", "zh_Hans"]
    fake_config.TRANSLATION_DIRS = Path(config.TEMP_DIR)

    # Use our config (and not an app fixture) because the i18n module
    # grabs values at init time and we can't inject them later.
    for app in (journalist_app_module.create_app(fake_config), source_app.create_app(fake_config)):
        with app.app_context():
            db.create_all()
        assert list(i18n.LOCALES.keys()) == fake_config.SUPPORTED_LOCALES
        verify_i18n(app)


def test_parse_locale_set():
    assert parse_locale_set([FALLBACK_LOCALE]) == set([Locale.parse(FALLBACK_LOCALE)])


def test_no_usable_fallback_locale(journalist_app, config):
    """
    The apps fail if neither the default nor the fallback locale is usable.
    """
    fake_config = SDConfig()
    fake_config.DEFAULT_LOCALE = NEVER_LOCALE
    fake_config.SUPPORTED_LOCALES = [NEVER_LOCALE]
    fake_config.TRANSLATION_DIRS = Path(config.TEMP_DIR)

    i18n.USABLE_LOCALES = set()

    with pytest.raises(ValueError, match="in the set of usable locales"):
        journalist_app_module.create_app(fake_config)

    with pytest.raises(ValueError, match="in the set of usable locales"):
        source_app.create_app(fake_config)


def test_unusable_default_but_usable_fallback_locale(config, caplog):
    """
    The apps start even if the default locale is unusable, as along as the fallback locale is
    usable, but log an error for OSSEC to pick up.
    """
    fake_config = SDConfig()
    fake_config.DEFAULT_LOCALE = NEVER_LOCALE
    fake_config.SUPPORTED_LOCALES = [NEVER_LOCALE, FALLBACK_LOCALE]
    fake_config.TRANSLATION_DIRS = Path(config.TEMP_DIR)

    for app in (journalist_app_module.create_app(fake_config), source_app.create_app(fake_config)):
        with app.app_context():
            assert NEVER_LOCALE in caplog.text
            assert "not in the set of usable locales" in caplog.text


def test_invalid_locales(config):
    """
    An invalid locale raises an error during app configuration.
    """
    fake_config = SDConfig()
    fake_config.SUPPORTED_LOCALES = [FALLBACK_LOCALE, "yy_ZZ"]
    fake_config.TRANSLATION_DIRS = Path(config.TEMP_DIR)

    with pytest.raises(UnknownLocaleError):
        journalist_app_module.create_app(fake_config)

    with pytest.raises(UnknownLocaleError):
        source_app.create_app(fake_config)


def test_valid_but_unusable_locales(config, caplog):
    """
    The apps start with one or more unusable, but still valid, locales, but log an error for
    OSSEC to pick up.
    """
    fake_config = SDConfig()

    fake_config.SUPPORTED_LOCALES = [FALLBACK_LOCALE, "wae_CH"]
    fake_config.TRANSLATION_DIRS = Path(config.TEMP_DIR)

    for app in (journalist_app_module.create_app(fake_config), source_app.create_app(fake_config)):
        with app.app_context():
            assert "wae" in caplog.text
            assert "not in the set of usable locales" in caplog.text


def test_language_tags():
    assert i18n.RequestLocaleInfo(Locale.parse("en")).language_tag == "en"
    assert i18n.RequestLocaleInfo(Locale.parse("en-US", sep="-")).language_tag == "en-US"
    assert i18n.RequestLocaleInfo(Locale.parse("en-us", sep="-")).language_tag == "en-US"
    assert i18n.RequestLocaleInfo(Locale.parse("en_US")).language_tag == "en-US"
    assert i18n.RequestLocaleInfo(Locale.parse("zh_Hant")).language_tag == "zh-Hant"


# Grab the journalist_app fixture to trigger creation of resources
def test_html_en_lang_correct(journalist_app, config):
    # Then delete it because using it won't test what we want
    del journalist_app

    app = journalist_app_module.create_app(config).test_client()
    resp = app.get("/", follow_redirects=True)
    html = resp.data.decode("utf-8")
    assert re.compile('<html lang="en-US".*>').search(html), html

    app = source_app.create_app(config).test_client()
    resp = app.get("/", follow_redirects=True)
    html = resp.data.decode("utf-8")
    assert re.compile('<html lang="en-US".*>').search(html), html

    # check '/generate' too because '/' uses a different template
    resp = app.post("/generate", data={"tor2web_check": 'href="fake.onion"'}, follow_redirects=True)
    html = resp.data.decode("utf-8")
    assert re.compile('<html lang="en-US".*>').search(html), html


# Grab the journalist_app fixture to trigger creation of resources
def test_html_fr_lang_correct(journalist_app, config):
    """Check that when the locale is fr_FR the lang property is correct"""

    # Then delete it because using it won't test what we want
    del journalist_app

    config.SUPPORTED_LOCALES = ["fr_FR", "en_US"]
    app = journalist_app_module.create_app(config).test_client()
    resp = app.get("/?l=fr_FR", follow_redirects=True)
    html = resp.data.decode("utf-8")
    assert re.compile('<html lang="fr-FR".*>').search(html), html

    app = source_app.create_app(config).test_client()
    resp = app.get("/?l=fr_FR", follow_redirects=True)
    html = resp.data.decode("utf-8")
    assert re.compile('<html lang="fr-FR".*>').search(html), html

    # check '/generate' too because '/' uses a different template
    resp = app.post(
        "/generate?l=fr_FR", data={"tor2web_check": 'href="fake.onion"'}, follow_redirects=True
    )
    html = resp.data.decode("utf-8")
    assert re.compile('<html lang="fr-FR".*>').search(html), html


# Grab the journalist_app fixture to trigger creation of resources
def test_html_attributes(journalist_app, config):
    """Check that HTML lang and dir attributes respect locale."""

    # Then delete it because using it won't test what we want
    del journalist_app

    config.SUPPORTED_LOCALES = ["ar", "en_US"]
    app = journalist_app_module.create_app(config).test_client()
    resp = app.get("/?l=ar", follow_redirects=True)
    html = resp.data.decode("utf-8")
    assert '<html lang="ar" dir="rtl">' in html
    resp = app.get("/?l=en_US", follow_redirects=True)
    html = resp.data.decode("utf-8")
    assert '<html lang="en-US" dir="ltr">' in html

    app = source_app.create_app(config).test_client()
    resp = app.get("/?l=ar", follow_redirects=True)
    html = resp.data.decode("utf-8")
    assert '<html lang="ar" dir="rtl">' in html
    resp = app.get("/?l=en_US", follow_redirects=True)
    html = resp.data.decode("utf-8")
    assert '<html lang="en-US" dir="ltr">' in html

    # check '/generate' too because '/' uses a different template
    resp = app.post(
        "/generate?l=ar", data={"tor2web_check": 'href="fake.onion"'}, follow_redirects=True
    )
    html = resp.data.decode("utf-8")
    assert '<html lang="ar" dir="rtl">' in html
    resp = app.post(
        "/generate?l=en_US", data={"tor2web_check": 'href="fake.onion"'}, follow_redirects=True
    )
    html = resp.data.decode("utf-8")
    assert '<html lang="en-US" dir="ltr">' in html


def test_same_lang_diff_locale(journalist_app, config):
    """
    Verify that when two locales with the same lang are specified, the full locale
    name is used for both.
    """
    del journalist_app
    config.SUPPORTED_LOCALES = ["en_US", "pt_BR", "pt_PT"]
    app = journalist_app_module.create_app(config).test_client()
    resp = app.get("/", follow_redirects=True)
    html = resp.data.decode("utf-8")
    assert "português (Brasil)" in html
    assert "português (Portugal)" in html
