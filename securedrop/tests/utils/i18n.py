import collections
import contextlib
import functools
import os
from typing import Dict, Generator, Iterable, List, Optional, Tuple

import pytest
from babel.core import (
    get_locale_identifier,
    parse_locale,
)
from babel.messages.catalog import Catalog
from babel.messages.pofile import read_po
from bs4 import BeautifulSoup
from flask_babel import force_locale

from sdconfig import SDConfig


@functools.lru_cache(maxsize=None)
def get_test_locales(default_locale: str = "en_US") -> List[str]:
    locales = set(os.environ.get("TEST_LOCALES", "ar en_US").split())
    locales.add(default_locale)
    return sorted(list(locales))


@functools.lru_cache(maxsize=None)
def get_plural_tests() -> Dict[str, Tuple[int, ...]]:
    return collections.defaultdict(
        lambda: (0, 1, 2),
        ar=(0, 1, 2, 3, 11, 100),
        cs=(1, 2, 5),
        ro=(0, 1, 2, 20),
        ru=(0, 1, 2, 20),
        sk=(0, 1, 2, 5, 10),
        zh_Hans=(1,),
        zh_Hant=(1,),
    )


def language_tag(locale: str) -> str:
    """
    Returns a BCP47/RFC5646 language tag for the locale.

    For example, it will convert "fr_FR" to "fr-FR".
    """
    return get_locale_identifier(parse_locale(locale), sep="-")


@functools.lru_cache(maxsize=None)
def message_catalog(config: SDConfig, locale: str) -> Catalog:
    """
    Returns the gettext message catalog for the given locale.

    With the catalog, tests can check whether a gettext call returned
    an actual translation or merely the result of falling back to the
    default locale.

    >>> german = message_catalog(config, 'de_DE')
    >>> m = german.get("a string that has been added to the catalog but not translated")
    >>> m.string
    ''
    >>> german.get("Password").string
    'Passwort'
    """
    return read_po(open(str(config.TRANSLATION_DIRS / locale / "LC_MESSAGES/messages.po")))


def page_language(page_text: str) -> Optional[str]:
    """
    Returns the "lang" attribute of the page's "html" element.
    """
    soup = BeautifulSoup(page_text, "html.parser")
    return soup.find("html").get("lang")


@contextlib.contextmanager
def xfail_untranslated_messages(config: SDConfig, locale: str, msgids: Iterable[str]) -> Generator:
    """
    Trigger pytest.xfail for untranslated strings.

    Given a list of gettext message IDs (strings marked for
    translation with gettext or ngettext in source code) used in this
    context manager's block, check that each has been translated in
    `locale`. Call pytest.xfail if any has not.

    Without this, to detect when gettext fell back to English, we'd
    have to hard-code the expected translations, which has obvious
    maintenance problems. You also can't just check that the result of
    a gettext call isn't the source string, because some translations
    are the same.
    """
    with force_locale(locale):
        if locale != "en_US":
            catalog = message_catalog(config, locale)
            for msgid in msgids:
                m = catalog.get(msgid)
                if not m:
                    pytest.xfail(
                        "locale {} message catalog lacks msgid: {}".format(locale, msgid)
                    )
                if not m.string:
                    pytest.xfail(
                        "locale {} has no translation for msgid: {}".format(locale, msgid)
                    )
        yield
