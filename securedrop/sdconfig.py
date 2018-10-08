# -*- coding: utf-8 -*-

import json
import os
import typing

from os import path

import config as _config

# https://www.python.org/dev/peps/pep-0484/#runtime-or-type-checking
if typing.TYPE_CHECKING:
    # flake8 can not understand type annotation yet.
    # That is why all type annotation relative import
    # statements has to be marked as noqa.
    # http://flake8.pycqa.org/en/latest/user/error-codes.html?highlight=f401
    from typing import List, Dict  # noqa: F401


CONFIG_FILE = '/etc/securedrop/config.json'


class _FlaskConfig(object):

    DEBUG = False
    TESTING = False
    WTF_CSRF_ENABLED = True

    def __init__(self, secret_key):
        # type: (str) -> None
        self.SECRET_KEY = secret_key


class _SourceInterfaceFlaskConfig(_FlaskConfig):

    SESSION_COOKIE_NAME = "ss"


class _JournalistInterfaceFlaskConfig(_FlaskConfig):

    SESSION_COOKIE_NAME = "js"


class SDConfig(object):


    def __init__(self):
        # type: () -> None

        with open(CONFIG_FILE) as f:
            json_config = json.loads(f.read())

        self.SECUREDROP_DATA_ROOT = '/var/lib/securedrop/'

        self.SECUREDROP_ROOT = path.abspath(path.dirname(__file__))

        journalist_secret = json_config['journalist_interface']['secret_key']  # type: ignore # noqa: 501
        self.JournalistInterfaceFlaskConfig = \
            _JournalistInterfaceFlaskConfig(journalist_secret)

        source_secret = json_config['source_interface']['secret_key']  # type: ignore # noqa: 501
        self.SourceInterfaceFlaskConfig = \
            _SourceInterfaceFlaskConfig(source_secret)

        self.SESSION_EXPIRATION_MINUTES = 120

        self.TRANSLATION_DIRS = path.join(self.SECUREDROP_ROOT, 'translations')

        self.WORKER_PIDFILE = '/tmp/securedrop_worker.pid'  # nosec: B108

        # also accessible via .source_interface.journalist_key
        self.JOURNALIST_KEY = json_config['journalist_interface']['journalist_key']  # noqa: 501

        try:
            # also accessible via .source_interface.i18n.default_locale
            self.DEFAULT_LOCALE = json_config['journalist_interface']['i18n']['default_locale'] # type: ignore # noqa: 501
        except (KeyError, TypeError):
            self.DEFAULT_LOCALE = 'en_US'

        try:
            # also accessible via .source_interface.i18n.supported_locales
            self.SUPPORTED_LOCALES = json_config['journalist_interface']['i18n']['supported_locales'] # type: ignore # noqa: 501
        except (KeyError, AttributeError):
            self.SUPPORTED_LOCALES = [self.DEFAULT_LOCALE]

        # also accessible via .source_interface.scrypt_gpg_pepper
        self.SCRYPT_GPG_PEPPER = json_config['journalist_interface']['scrypt_gpg_pepper'] # type: ignore # noqa: 501

        # also accessible via .source_interface.scrypt_id_pepper
        self.SCRYPT_ID_PEPPER = json_config['journalist_interface']['scrypt_id_pepper'] # type: ignore # noqa: 501

        # also accessible via .source_interface.scrypt_params
        try:
            self.SCRYPT_PARAMS = json_config['journalist_interface']['scrypt_params'] # type: ignore # noqa: 501
        except (KeyError, TypeError):
            self.SCRYPT_PARAMS = dict(N=2**14, r=8, p=1)

        try:
            # also accessible via .source_interface.custom_header_image
            self.CUSTOM_HEADER_IMAGE = json_config['journalist_interface']['custom_header_image'] # type: ignore # noqa: 501
        except (KeyError, TypeError):
            self.CUSTOM_HEADER_IMAGE = None

        self.env = os.environ.get('SECUREDROP_ENV', 'prod')

        if self.env == 'prod':
            # This is recommended for performance, and also resolves #369
            _FlaskConfig.USE_X_SENDFILE = True  # type: ignore
        elif self.env == 'dev':
            # Enable _Flask's debugger for development
            _FlaskConfig.DEBUG = True
            # Use MAX_CONTENT_LENGTH to mimic the behavior of Apache's LimitRequestBody  # noqa: 501
            # in the development environment. See #1714.
            _FlaskConfig.MAX_CONTENT_LENGTH = 524288000  # type: ignore
        elif self.env == 'test':
            _FlaskConfig.TESTING = True
            # Disable CSRF checks to make writing tests easier
            _FlaskConfig.WTF_CSRF_ENABLED = False

    @property
    def DATABASE_FILE(self):
        return path.join(self.SECUREDROP_DATA_ROOT, 'db.sqlite')

    @DATABASE_FILE.setter
    def DATABASE_FILE(self, value):
        raise AttributeError('Cannot set DATABASE_FILE')

    @DATABASE_FILE.deleter
    def DATABASE_FILE(self):
        raise AttributeError('Cannot delete DATABASE_FILE')

    @property
    def ADJECTIVES(self):
        return path.join(self.SECUREDROP_ROOT, 'dictionaries',
                         'adjectives.txt')

    @ADJECTIVES.setter
    def ADJECTIVES(self, value):
        raise AttributeError('Cannot set ADJECTIVES')

    @ADJECTIVES.deleter
    def ADJECTIVES(self):
        raise AttributeError('Cannot delete ADJECTIVES')

    @property
    def NOUNS(self):
        return path.join(self.SECUREDROP_ROOT, 'dictionaries', 'nouns.txt')

    @NOUNS.setter
    def NOUNS(self, value):
        raise AttributeError('Cannot set NOUNS')

    @NOUNS.deleter
    def NOUNS(self):
        raise AttributeError('Cannot delete NOUNS')

    @property
    def GPG_KEY_DIR(self):
        return path.join(self.SECUREDROP_DATA_ROOT, 'keys')

    @GPG_KEY_DIR.setter
    def GPG_KEY_DIR(self, value):
        raise AttributeError('Cannot set GPG_KEY_DIR')

    @GPG_KEY_DIR.deleter
    def GPG_KEY_DIR(self):
        raise AttributeError('Cannot delete GPG_KEY_DIR')

    @property
    def JOURNALIST_TEMPLATES_DIR(self):
        return path.join(self.SECUREDROP_ROOT, 'journalist_templates')

    @JOURNALIST_TEMPLATES_DIR.setter
    def JOURNALIST_TEMPLATES_DIR(self, value):
        raise AttributeError('Cannot set JOURNALIST_TEMPLATES_DIR')

    @JOURNALIST_TEMPLATES_DIR.deleter
    def JOURNALIST_TEMPLATES_DIR(self):
        raise AttributeError('Cannot delete JOURNALIST_TEMPLATES_DIR')

    @property
    def SOURCE_TEMPLATES_DIR(self):
        return path.join(self.SECUREDROP_ROOT, 'source_templates')

    @SOURCE_TEMPLATES_DIR.setter
    def SOURCE_TEMPLATES_DIR(self, value):
        raise AttributeError('Cannot set SOURCE_TEMPLATES_DIR')

    @SOURCE_TEMPLATES_DIR.deleter
    def SOURCE_TEMPLATES_DIR(self):
        raise AttributeError('Cannot delete SOURCE_TEMPLATES_DIR')

    @property
    def TEMP_DIR(self):
        return path.join(self.SECUREDROP_DATA_ROOT, 'tmp')

    @TEMP_DIR.setter
    def TEMP_DIR(self, value):
        raise AttributeError('Cannot set TEMP_DIR')

    @TEMP_DIR.deleter
    def TEMP_DIR(self):
        raise AttributeError('Cannot delete TEMP_DIR')

    @property
    def STORE_DIR(self):
        return path.join(self.SECUREDROP_DATA_ROOT, 'store')

    @STORE_DIR.setter
    def STORE_DIR(self, value):
        raise AttributeError('Cannot set STORE_DIR')

    @STORE_DIR.deleter
    def STORE_DIR(self):
        raise AttributeError('Cannot delete STORE_DIR')

    @property
    def WORD_LIST(self):
        return path.join(self.SECUREDROP_ROOT, 'wordlist')

    @WORD_LIST.setter
    def WORD_LIST(self, value):
        raise AttributeError('Cannot set WORD_LIST')

    @WORD_LIST.deleter
    def WORD_LIST(self):
        raise AttributeError('Cannot delete WORD_LIST')

config = SDConfig()  # type: SDConfig
