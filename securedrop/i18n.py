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
import collections
from typing import Dict, List, Set

from babel.core import (
    Locale,
    UnknownLocaleError,
    get_locale_identifier,
    negotiate_locale,
    parse_locale,
)
from flask import Flask, g, request, session
from flask_babel import Babel
from sdconfig import FALLBACK_LOCALE, SDConfig


class RequestLocaleInfo:
    """
    Convenience wrapper around a babel.core.Locale.
    """

    def __init__(self, locale: str):
        self.locale = Locale.parse(locale)

        # This attribute can be set to `True` to differentiate multiple
        # locales currently available (supported) for the same language.
        self.use_display_name = False

    def __str__(self) -> str:
        """
        The Babel string representation of the locale.
        """
        return str(self.locale)

    @property
    def display_name(self) -> str:
        """
        Give callers (i.e., templates) the `Locale` object's display name when
        such resolution is warranted, otherwise the language name---as
        determined by `map_locale_display_names()`.
        """
        if self.use_display_name:
            return self.locale.display_name
        return self.locale.language_name

    @property
    def text_direction(self) -> str:
        """
        The Babel text direction: ltr or rtl.

        Used primarily to set text direction in HTML via the "dir"
        attribute.
        """
        return self.locale.text_direction

    @property
    def language(self) -> str:
        """
        The Babel language name.

        Just the language, without subtag info like region or script.
        """
        return self.locale.language

    @property
    def id(self) -> str:
        """
        The Babel string representation of the locale.

        This should match the name of the directory containing its
        translations.
        """
        return str(self.locale)

    @property
    def language_tag(self) -> str:
        """
        Returns a BCP47/RFC5646 language tag for the locale.

        Language tags are used in HTTP headers and the HTML lang
        attribute.
        """
        return get_locale_identifier(parse_locale(str(self.locale)), sep="-")


def configure_babel(config: SDConfig, app: Flask) -> Babel:
    """
    Set up Flask-Babel according to the SecureDrop configuration.
    """
    # Tell Babel where to find our translations.
    translations_directory = str(config.TRANSLATION_DIRS.absolute())
    app.config["BABEL_TRANSLATION_DIRECTORIES"] = translations_directory

    # Create the app's Babel instance. Passing the app to the
    # constructor causes the instance to attach itself to the app.
    babel = Babel(app)

    # verify that Babel is only using the translations we told it about
    if list(babel.translation_directories) != [translations_directory]:
        raise ValueError(
            "Babel translation directories ({}) do not match SecureDrop configuration ({})".format(
                babel.translation_directories, [translations_directory]
            )
        )

    # register the function used to determine the locale of a request
    babel.localeselector(lambda: get_locale(config))
    return babel


def parse_locale_set(codes: List[str]) -> Set[Locale]:
    return {Locale.parse(code) for code in codes}


def validate_locale_configuration(config: SDConfig, babel: Babel) -> None:
    """
    Check that configured locales are available in the filesystem and therefore usable by
    Babel.  Warn about configured locales that are not usable, unless we're left with
    no usable default or fallback locale, in which case raise an exception.
    """
    # These locales are available and loadable from the filesystem.
    available = set(babel.list_translations())
    available.add(Locale.parse(FALLBACK_LOCALE))

    # These locales were configured via "securedrop-admin sdconfig", meaning
    # they were present on the Admin Workstation at "securedrop-admin" runtime.
    configured = parse_locale_set(config.SUPPORTED_LOCALES)

    # The intersection of these sets is the set of locales usable by Babel.
    usable = available & configured

    missing = configured - usable
    if missing:
        babel.app.logger.error(
            f"Configured locales {missing} are not in the set of usable locales {usable}"
        )

    defaults = parse_locale_set([config.DEFAULT_LOCALE, FALLBACK_LOCALE])
    if not defaults & usable:
        raise ValueError(
            f"None of the default locales {defaults} are in the set of usable locales {usable}"
        )

    global USABLE_LOCALES
    USABLE_LOCALES = usable


# TODO(#6420): avoid relying on and manipulating on this global state
LOCALES = collections.OrderedDict()  # type: collections.OrderedDict[str, RequestLocaleInfo]
USABLE_LOCALES = set()  # type: Set[Locale]


def map_locale_display_names(config: SDConfig) -> None:
    """
    Create a map of locale identifiers to names for display.

    For most of our supported languages, we only provide one
    translation, so including the full display name is not necessary
    to distinguish them. For languages with more than one translation,
    like Chinese, we do need the additional detail.
    """

    language_locale_counts = collections.defaultdict(int)  # type: Dict[str, int]
    for l in sorted(config.SUPPORTED_LOCALES):
        locale = RequestLocaleInfo(l)
        language_locale_counts[locale.language] += 1

    locale_map = collections.OrderedDict()
    for l in sorted(config.SUPPORTED_LOCALES):
        if Locale.parse(l) not in USABLE_LOCALES:
            continue

        locale = RequestLocaleInfo(l)
        if language_locale_counts[locale.language] > 1:
            # Disambiguate translations for this language.
            locale.use_display_name = True

        locale_map[str(locale)] = locale

    global LOCALES
    LOCALES = locale_map


def configure(config: SDConfig, app: Flask) -> None:
    babel = configure_babel(config, app)
    validate_locale_configuration(config, babel)
    map_locale_display_names(config)


def get_locale(config: SDConfig) -> str:
    """
    Return the best supported locale for a request.

    Get the locale as follows, by order of precedence:
    - l request argument or session['locale']
    - browser suggested locale, from the Accept-Languages header
    - config.DEFAULT_LOCALE
    - config.FALLBACK_LOCALE
    """
    preferences = []
    if session and session.get("locale"):
        preferences.append(session.get("locale"))
    if request.args.get("l"):
        preferences.insert(0, request.args.get("l"))
    if not preferences:
        preferences.extend(get_accepted_languages())
    preferences.append(config.DEFAULT_LOCALE)
    preferences.append(FALLBACK_LOCALE)

    negotiated = negotiate_locale(preferences, LOCALES.keys())

    if not negotiated:
        raise ValueError("No usable locale")

    return negotiated


def get_accepted_languages() -> List[str]:
    """
    Convert a request's list of accepted languages into locale identifiers.
    """
    accept_languages = []
    for l in request.accept_languages.values():
        try:
            parsed = Locale.parse(l, "-")
            accept_languages.append(str(parsed))

            # We only have two Chinese translations, simplified
            # and traditional, based on script and not
            # region. Browsers tend to send identifiers with
            # region, e.g. zh-CN or zh-TW. Babel can generally
            # infer the script from those, so we can fabricate a
            # fallback entry without region, in the hope that it
            # will match one of our translations and the site will
            # at least be more legible at first contact than the
            # probable default locale of English.
            if parsed.language == "zh" and parsed.script:
                accept_languages.append(str(Locale(language=parsed.language, script=parsed.script)))
        except (ValueError, UnknownLocaleError):
            pass
    return accept_languages


def set_locale(config: SDConfig) -> None:
    """
    Update locale info in request and session.
    """
    locale = get_locale(config)
    g.localeinfo = RequestLocaleInfo(locale)  # pylint: disable=assigning-non-slot
    session["locale"] = locale
    g.locales = LOCALES  # pylint: disable=assigning-non-slot
