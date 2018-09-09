# -*- coding: utf-8 -*-

import json
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


class SDConfig(object):
    def __init__(self):
        # type: () -> None

        with open(CONFIG_FILE) as f:
            json_config = json.loads(f.read())

        self.SECUREDROP_DATA_ROOT = '/var/lib/securedrop/'

        self.SECUREDROP_ROOT = path.abspath(path.dirname(__file__))

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
            self.ADJECTIVES = _config.ADJECTIVES  # type: ignore
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

    @property
    def DATABASE_FILE(self):
        return path.join(self.SECUREDROP_DATA_ROOT, 'db.sqlite')

    @DATABASE_FILE.setter
    def DATABASE_FILE(self, value):
        raise AttributeError('Cannot set DATABASE_FILE')

    @DATABASE_FILE.deleter
    def DATABASE_FILE(self):
        raise AttributeError('Cannot delete DATABASE_FILE')


config = SDConfig()  # type: SDConfig
