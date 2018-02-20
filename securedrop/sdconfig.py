# -*- coding: utf-8 -*-

import config as _config

import typing
# https://www.python.org/dev/peps/pep-0484/#runtime-or-type-checking
if typing.TYPE_CHECKING:
    # flake8 can not understand type annotation yet.
    # That is why all type annotation realted import
    # statements has to be marked as noqa.
    # http://flake8.pycqa.org/en/latest/user/error-codes.html?highlight=f401
    from typing import List, Dict  # noqa: F401


class SDConfig(object):
    def __init__(self):
        # type: () -> None
        if hasattr(_config, 'FlaskConfig'):
            self.FlaskConfig = _config.FlaskConfig  # type: ignore

        if hasattr(_config, 'JournalistInterfaceFlaskConfig'):
            self.JournalistInterfaceFlaskConfig = \
                _config.JournalistInterfaceFlaskConfig  # type: ignore

        if hasattr(_config, 'SourceInterfaceFlaskConfig'):
            self.SourceInterfaceFlaskConfig = \
                _config.SourceInterfaceFlaskConfig  # type: ignore

        if hasattr(_config, "DATABASE_ENGINE"):
            self.DATABASE_ENGINE = _config.DATABASE_ENGINE  # type: ignore

        if hasattr(_config, "DATABASE_FILE"):
            self.DATABASE_FILE = _config.DATABASE_FILE  # type: ignore

        if hasattr(_config, "DATABASE_USERNAME"):
            self.DATABASE_USERNAME = _config.DATABASE_USERNAME  # type: ignore

        if hasattr(_config, "DATABASE_PASSWORD"):
            self.DATABASE_PASSWORD = _config.DATABASE_PASSWORD  # type: ignore

        if hasattr(_config, "DATABASE_HOST"):
            self.DATABASE_HOST = _config.DATABASE_HOST  # type: ignore

        if hasattr(_config, "DATABASE_NAME"):
            self.DATABASE_NAME = _config.DATABASE_NAME  # type: ignore

        if hasattr(_config, 'CUSTOM_HEADER_IMAGE'):
            self.CUSTOM_HEADER_IMAGE = \
                _config.CUSTOM_HEADER_IMAGE  # type: ignore

        if hasattr(_config, 'SUPPORTED_LOCALES'):
            self.SUPPORTED_LOCALES = \
                _config.SUPPORTED_LOCALES  # type: ignore

        # Now we will fill up existing values from config.py
        if hasattr(_config, "ADJECTIVES"):
            self.ADJECTIVES = _config.ADJECTIVES  # type: str

        if hasattr(_config, "DATABASE_ENGINE"):
            self.DATABASE_ENGINE = _config.DATABASE_ENGINE  # type: str

        if hasattr(_config, "DATABASE_FILE"):
            self.DATABASE_FILE = _config.DATABASE_FILE  # type: str

        if hasattr(_config, "DEFAULT_LOCALE"):
            self.DEFAULT_LOCALE = _config.DEFAULT_LOCALE  # type: ignore

        if hasattr(_config, "GPG_KEY_DIR"):
            self.GPG_KEY_DIR = _config.GPG_KEY_DIR  # type: str

        if hasattr(_config, "JOURNALIST_KEY"):
            self.JOURNALIST_KEY = _config.JOURNALIST_KEY  # type: str

        if hasattr(_config, "JOURNALIST_TEMPLATES_DIR"):
            self.JOURNALIST_TEMPLATES_DIR = \
                _config.JOURNALIST_TEMPLATES_DIR  # type: str

        if hasattr(_config, "NOUNS"):
            self.NOUNS = _config.NOUNS  # type: str

        if hasattr(_config, "SCRYPT_GPG_PEPPER"):
            self.SCRYPT_GPG_PEPPER = _config.SCRYPT_GPG_PEPPER  # type: str

        if hasattr(_config, "SCRYPT_ID_PEPPER"):
            self.SCRYPT_ID_PEPPER = _config.SCRYPT_ID_PEPPER  # type: str

        if hasattr(_config, "SCRYPT_PARAMS"):
            self.SCRYPT_PARAMS = _config.SCRYPT_PARAMS  # type: Dict[str,int]

        if hasattr(_config, "SECUREDROP_DATA_ROOT"):
            self.SECUREDROP_DATA_ROOT = \
                _config.SECUREDROP_DATA_ROOT  # type: str

        if hasattr(_config, "SECUREDROP_ROOT"):
            self.SECUREDROP_ROOT = _config.SECUREDROP_ROOT  # type: str

        if hasattr(_config, "SESSION_EXPIRATION_MINUTES"):
            self.SESSION_EXPIRATION_MINUTES = \
                _config.SESSION_EXPIRATION_MINUTES  # type: ignore

        if hasattr(_config, "SOURCE_TEMPLATES_DIR"):
            self.SOURCE_TEMPLATES_DIR = \
                _config.SOURCE_TEMPLATES_DIR   # type: str

        if hasattr(_config, "STORE_DIR"):
            self.STORE_DIR = _config.STORE_DIR  # type: str

        if hasattr(_config, "SUPPORTED_LOCALES"):
            self.SUPPORTED_LOCALES = _config.SUPPORTED_LOCALES  # type: ignore

        if hasattr(_config, "TEMP_DIR"):
            self.TEMP_DIR = _config.TEMP_DIR  # type: str

        if hasattr(_config, "WORD_LIST"):
            self.WORD_LIST = _config.WORD_LIST  # type: str

        if hasattr(_config, "WORKER_PIDFILE"):
            self.WORKER_PIDFILE = _config.WORKER_PIDFILE  # type: str

        if hasattr(_config, "TRANSLATION_DIRS"):
            self.TRANSLATION_DIRS = _config.TRANSLATION_DIRS  # type: ignore

        if hasattr(_config, "env"):
            self.env = _config.env  # type: str


config = SDConfig()  # type: SDConfig
