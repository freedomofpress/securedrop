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
import re
import subprocess
from pathlib import Path
from typing import List

import i18n
import journalist_app as journalist_app_module
import pytest
import source_app
from babel.core import Locale, UnknownLocaleError
from db import db
from flask import render_template, render_template_string, request, session
from flask_babel import gettext
from i18n import parse_locale_set
from sdconfig import DEFAULT_SECUREDROP_ROOT, FALLBACK_LOCALE, SecureDropConfig
from tests.factories import SecureDropConfigFactory
from werkzeug.datastructures import Headers

# Interlingua, per
# <https://developers.securedrop.org/en/latest/supported_languages.html>.
NEVER_LOCALE = "ia"


def create_config_for_i18n_test(
    supported_locales: List[str],
    default_locale: str = "en_US",
    translation_dirs: Path = DEFAULT_SECUREDROP_ROOT / "translations",
) -> SecureDropConfig:
    tmp_root_for_test = Path("/tmp/sd-tests/test_i18n")
    tmp_root_for_test.mkdir(exist_ok=True, parents=True)

    i18n_config = SecureDropConfigFactory.create(
        SECUREDROP_DATA_ROOT=tmp_root_for_test,
        DEFAULT_LOCALE=default_locale,
        SUPPORTED_LOCALES=supported_locales,
        TRANSLATION_DIRS=translation_dirs,
        # For the tests in these files, the following argument / config fields are not used so
        # we set them to invalid values
        RQ_WORKER_NAME="",
        GPG_KEY_DIR=tmp_root_for_test,
        JOURNALIST_KEY="",
    )

    # Create an empty key file just to pass the sanity checks when starting the source or
    # journalist app; the encryption code is not exercised as part of these tests
    gpg_key_path = tmp_root_for_test / "private-keys-v1.d"
    gpg_key_path.mkdir(exist_ok=True)

    return i18n_config


def set_msg_translation_in_po_file(po_file: Path, msgid_to_translate: str, msgstr: str) -> None:
    po_content = po_file.read_text()
    content_to_update = f"""
msgid "{msgid_to_translate}"
msgstr ""
"""
    assert content_to_update in po_content

    content_with_translation = f"""
msgid "{msgid_to_translate}"
msgstr "{msgstr}"
"""
    po_content_with_translation = po_content.replace(content_to_update, content_with_translation)
    po_file.write_text(po_content_with_translation)


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
        assert render_template("locales.html") == ""

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
        # We have to render a template that inherits from "base.html" so that "tab_title" will be
        # set.  But we're just checking that when a page is rendered in an RTL language the
        # directionality is correct, so it doesn't matter which template we render.
        base = render_template("error.html", error={})
        assert 'dir="rtl"' in base


def test_i18n():
    translation_dirs = Path("/tmp/sd-tests/test_i18n/translations")
    translation_dirs.mkdir(exist_ok=True, parents=True)
    test_config = create_config_for_i18n_test(
        supported_locales=["ar", "en_US", "fr_FR", "nb_NO", "zh_Hans"],
        translation_dirs=translation_dirs,
    )

    i18n_dir = Path(__file__).absolute().parent / "i18n"
    sources = [str(i18n_dir / "code.py"), str(i18n_dir / "template.html")]
    pot = i18n_dir / "messages.pot"
    subprocess.check_call(
        [
            "pybabel",
            "extract",
            "--mapping",
            str(i18n_dir / "babel.cfg"),
            "--output",
            pot,
            *sources,
        ]
    )

    subprocess.check_call(
        [
            "pybabel",
            "init",
            "--input-file",
            pot,
            "--output-dir",
            translation_dirs,
            "--locale",
            "en_US",
        ]
    )

    for locale, translated_msg in (
        ("fr_FR", "code bonjour"),
        ("zh_Hans", "code chinese"),
        ("ar", "code arabic"),
        ("nb_NO", "code norwegian"),
        ("es_ES", "code spanish"),
    ):
        subprocess.check_call(
            [
                "pybabel",
                "init",
                "--input-file",
                pot,
                "--output-dir",
                translation_dirs,
                "--locale",
                locale,
            ]
        )

        # Populate the po file with a translation
        po_file = translation_dirs / locale / "LC_MESSAGES" / "messages.po"
        set_msg_translation_in_po_file(
            po_file,
            msgid_to_translate="code hello i18n",
            msgstr=translated_msg,
        )

        subprocess.check_call(
            [
                "pybabel",
                "compile",
                "--directory",
                translation_dirs,
                "--locale",
                locale,
                "--input-file",
                po_file,
            ]
        )

    # Use our config (and not an app fixture) because the i18n module
    # grabs values at init time and we can't inject them later.
    for app in (
        journalist_app_module.create_app(test_config),
        source_app.create_app(test_config),
    ):
        with app.app_context():
            db.create_all()
        assert list(app.config["LOCALES"].keys()) == test_config.SUPPORTED_LOCALES
        verify_i18n(app)


def test_parse_locale_set():
    assert parse_locale_set([FALLBACK_LOCALE]) == {Locale.parse(FALLBACK_LOCALE)}


def test_no_usable_fallback_locale():
    """
    The apps fail if neither the default nor the fallback locale is usable.
    """
    test_config = create_config_for_i18n_test(
        default_locale=NEVER_LOCALE, supported_locales=[NEVER_LOCALE]
    )

    with pytest.raises(ValueError, match="in the set of usable locales"):
        journalist_app_module.create_app(test_config)

    with pytest.raises(ValueError, match="in the set of usable locales"):
        source_app.create_app(test_config)


def test_unusable_default_but_usable_fallback_locale(caplog):
    """
    The apps start even if the default locale is unusable, as along as the fallback locale is
    usable, but log an error for OSSEC to pick up.
    """
    test_config = create_config_for_i18n_test(
        default_locale=NEVER_LOCALE, supported_locales=[NEVER_LOCALE, FALLBACK_LOCALE]
    )

    for app in (journalist_app_module.create_app(test_config), source_app.create_app(test_config)):
        with app.app_context():
            assert NEVER_LOCALE in caplog.text
            assert "not in the set of usable locales" in caplog.text


def test_invalid_locales():
    """
    An invalid locale raises an error during app configuration.
    """
    test_config = create_config_for_i18n_test(supported_locales=[FALLBACK_LOCALE, "yy_ZZ"])

    with pytest.raises(UnknownLocaleError):
        journalist_app_module.create_app(test_config)

    with pytest.raises(UnknownLocaleError):
        source_app.create_app(test_config)


def test_valid_but_unusable_locales(caplog):
    """
    The apps start with one or more unusable, but still valid, locales, but log an error for
    OSSEC to pick up.
    """
    test_config = create_config_for_i18n_test(
        supported_locales=[FALLBACK_LOCALE, "wae_CH"],
    )

    for app in (journalist_app_module.create_app(test_config), source_app.create_app(test_config)):
        with app.app_context():
            assert "wae" in caplog.text
            assert "not in the set of usable locales" in caplog.text


def test_language_tags():
    assert i18n.RequestLocaleInfo(Locale.parse("en")).language_tag == "en"
    assert i18n.RequestLocaleInfo(Locale.parse("en-US", sep="-")).language_tag == "en-US"
    assert i18n.RequestLocaleInfo(Locale.parse("en-us", sep="-")).language_tag == "en-US"
    assert i18n.RequestLocaleInfo(Locale.parse("en_US")).language_tag == "en-US"
    assert i18n.RequestLocaleInfo(Locale.parse("zh_Hant")).language_tag == "zh-Hant"


def test_html_en_lang_correct():
    test_config = create_config_for_i18n_test(supported_locales=["en_US"])
    app = journalist_app_module.create_app(test_config).test_client()
    resp = app.get("/", follow_redirects=True)
    html = resp.data.decode("utf-8")
    assert re.compile('<html lang="en-US".*>').search(html), html

    app = source_app.create_app(test_config).test_client()
    resp = app.get("/", follow_redirects=True)
    html = resp.data.decode("utf-8")
    assert re.compile('<html lang="en-US".*>').search(html), html

    # check '/generate' too because '/' uses a different template
    resp = app.post("/generate", data={"tor2web_check": 'href="fake.onion"'}, follow_redirects=True)
    html = resp.data.decode("utf-8")
    assert re.compile('<html lang="en-US".*>').search(html), html


def test_html_fr_lang_correct():
    """Check that when the locale is fr_FR the lang property is correct"""
    test_config = create_config_for_i18n_test(supported_locales=["fr_FR", "en_US"])

    app = journalist_app_module.create_app(test_config).test_client()
    resp = app.get("/?l=fr_FR", follow_redirects=True)
    html = resp.data.decode("utf-8")
    assert re.compile('<html lang="fr-FR".*>').search(html), html

    app = source_app.create_app(test_config).test_client()
    resp = app.get("/?l=fr_FR", follow_redirects=True)
    html = resp.data.decode("utf-8")
    assert re.compile('<html lang="fr-FR".*>').search(html), html

    # check '/generate' too because '/' uses a different template
    resp = app.post(
        "/generate?l=fr_FR", data={"tor2web_check": 'href="fake.onion"'}, follow_redirects=True
    )
    html = resp.data.decode("utf-8")
    assert re.compile('<html lang="fr-FR".*>').search(html), html


def test_html_attributes():
    """Check that HTML lang and dir attributes respect locale."""
    test_config = create_config_for_i18n_test(supported_locales=["ar", "en_US"])

    app = journalist_app_module.create_app(test_config).test_client()
    resp = app.get("/?l=ar", follow_redirects=True)
    html = resp.data.decode("utf-8")
    assert '<html lang="ar" dir="rtl">' in html
    resp = app.get("/?l=en_US", follow_redirects=True)
    html = resp.data.decode("utf-8")
    assert '<html lang="en-US" dir="ltr">' in html

    app = source_app.create_app(test_config).test_client()
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


def test_same_lang_diff_locale():
    """
    Verify that when two locales with the same lang are specified, the full locale
    name is used for both.
    """
    test_config = create_config_for_i18n_test(supported_locales=["en_US", "pt_BR", "pt_PT"])

    app = journalist_app_module.create_app(test_config).test_client()
    resp = app.get("/", follow_redirects=True)
    html = resp.data.decode("utf-8")
    assert "português (Brasil)" in html
    assert "português (Portugal)" in html


def test_duplicate_locales():
    """
    Verify that we don't display the full locale name for duplicate locales,
    whether from user input or securedrop.sdconfig's enforcement of the
    fallback locale.
    """

    # ["en_US", "en_US"] alone will not display the locale switcher, which
    # *does* pass through set deduplication.
    test_config = create_config_for_i18n_test(supported_locales=["en_US", "en_US", "ar"])

    app = journalist_app_module.create_app(test_config).test_client()
    resp = app.get("/", follow_redirects=True)
    html = resp.data.decode("utf-8")
    assert "English (United States)" not in html
