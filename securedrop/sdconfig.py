# -*- coding: utf-8 -*-

import config as _config

import typing
# https://www.python.org/dev/peps/pep-0484/#runtime-or-type-checking
if typing.TYPE_CHECKING:
    # flake8 can not understand type annotation yet.
    # That is why all type annotation relative import
    # statements has to be marked as noqa.
    # http://flake8.pycqa.org/en/latest/user/error-codes.html?highlight=f401
    from typing import List, Dict  # noqa: F401


class SDConfig(object):
    def __init__(self) -> None:
        try:
            self.JournalistInterfaceFlaskConfig = \
                _config.JournalistInterfaceFlaskConfig  # type: ignore
        except AttributeError:
            pass

        try:
            self.SourceInterfaceFlaskConfig = \
                _config.SourceInterfaceFlaskConfig  # type: ignore
        except AttributeError:
            pass

        try:
            self.DATABASE_FILE = _config.DATABASE_FILE  # type: ignore
        except AttributeError:
            pass

        try:
            self.DATABASE_USERNAME = _config.DATABASE_USERNAME  # type: ignore
        except AttributeError:
            pass

        try:
            self.DATABASE_PASSWORD = _config.DATABASE_PASSWORD  # type: ignore
        except AttributeError:
            pass

        try:
            self.DATABASE_HOST = _config.DATABASE_HOST  # type: ignore
        except AttributeError:
            pass

        try:
            self.DATABASE_NAME = _config.DATABASE_NAME  # type: ignore
        except AttributeError:
            pass

        try:
            self.ADJECTIVES = _config.ADJECTIVES  # type: ignore
        except AttributeError:
            pass

        try:
            self.DATABASE_ENGINE = _config.DATABASE_ENGINE  # type: ignore
        except AttributeError:
            pass

        try:
            self.DEFAULT_LOCALE = _config.DEFAULT_LOCALE  # type: ignore
        except AttributeError:
            pass

        try:
            self.GPG_KEY_DIR = _config.GPG_KEY_DIR  # type: ignore
        except AttributeError:
            pass

        try:
            self.JOURNALIST_KEY = _config.JOURNALIST_KEY  # type: ignore
        except AttributeError:
            pass

        try:
            self.JOURNALIST_TEMPLATES_DIR = _config.JOURNALIST_TEMPLATES_DIR  # type: ignore # noqa: E501
        except AttributeError:
            pass

        try:
            self.NOUNS = _config.NOUNS  # type: ignore
        except AttributeError:
            pass

        try:
            self.SCRYPT_GPG_PEPPER = _config.SCRYPT_GPG_PEPPER  # type: ignore
        except AttributeError:
            pass

        try:
            self.SCRYPT_ID_PEPPER = _config.SCRYPT_ID_PEPPER  # type: ignore
        except AttributeError:
            pass

        try:
            self.SCRYPT_PARAMS = _config.SCRYPT_PARAMS  # type: ignore
        except AttributeError:
            pass

        try:
            self.SECUREDROP_DATA_ROOT = _config.SECUREDROP_DATA_ROOT  # type: ignore # noqa: E501
        except AttributeError:
            pass

        try:
            self.SECUREDROP_ROOT = _config.SECUREDROP_ROOT  # type: ignore
        except AttributeError:
            pass

        try:
            self.SESSION_EXPIRATION_MINUTES = \
                _config.SESSION_EXPIRATION_MINUTES  # type: ignore
        except AttributeError:
            pass

        try:
            self.SOURCE_TEMPLATES_DIR = \
                _config.SOURCE_TEMPLATES_DIR  # type: ignore
        except AttributeError:
            pass

        try:
            self.STORE_DIR = _config.STORE_DIR  # type: ignore
        except AttributeError:
            pass

        try:
            self.SUPPORTED_LOCALES = \
                _config.SUPPORTED_LOCALES  # type: ignore
        except AttributeError:
            pass

        try:
            self.TEMP_DIR = _config.TEMP_DIR  # type: ignore
        except AttributeError:
            pass

        try:
            self.WORD_LIST = _config.WORD_LIST  # type: ignore
        except AttributeError:
            pass

        try:
            self.WORKER_PIDFILE = _config.WORKER_PIDFILE  # type: ignore
        except AttributeError:
            pass

        try:
            self.TRANSLATION_DIRS = _config.TRANSLATION_DIRS  # type: ignore
        except AttributeError:
            pass

        try:
            self.env = _config.env  # type: ignore
        except AttributeError:
            pass

        if getattr(self, 'env', 'prod') == 'test':
            self.RQ_WORKER_NAME = 'test'
        else:
            self.RQ_WORKER_NAME = 'default'


config = SDConfig()  # type: SDConfig
