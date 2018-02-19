# -*- coding: utf-8 -*-

import config as _config

MYPY = False
if MYPY:
    from typing import List  # noqa: F401


class SDConfig(object):
    def __init__(self):
        # type: () -> None
        self.ADJECTIVES = _config.ADJECTIVES
        self.DATABASE_ENGINE = _config.DATABASE_ENGINE
        self.DEFAULT_LOCALE = _config.DEFAULT_LOCALE
        self.FlaskConfig = _config.FlaskConfig
        self.GPG_KEY_DIR = _config.GPG_KEY_DIR
        self.JOURNALIST_KEY = _config.JOURNALIST_KEY
        self.JOURNALIST_TEMPLATES_DIR = _config.JOURNALIST_TEMPLATES_DIR
        self.JournalistInterfaceFlaskConfig = \
            _config.JournalistInterfaceFlaskConfig
        self.NOUNS = _config.NOUNS
        self.SCRYPT_GPG_PEPPER = _config.SCRYPT_GPG_PEPPER
        self.SCRYPT_ID_PEPPER = _config.SCRYPT_ID_PEPPER
        self.SCRYPT_PARAMS = _config.SCRYPT_PARAMS
        self.SECUREDROP_DATA_ROOT = _config.SECUREDROP_DATA_ROOT
        self.SECUREDROP_ROOT = _config.SECUREDROP_ROOT
        self.SESSION_EXPIRATION_MINUTES = _config.SESSION_EXPIRATION_MINUTES
        self.SOURCE_TEMPLATES_DIR = _config.SOURCE_TEMPLATES_DIR
        self.STORE_DIR = _config.STORE_DIR
        self.SUPPORTED_LOCALES = []  # type: List[str]
        self.SourceInterfaceFlaskConfig = _config.SourceInterfaceFlaskConfig
        self.TEMP_DIR = _config.TEMP_DIR
        self.WORD_LIST = _config.WORD_LIST
        self.WORKER_PIDFILE = _config.WORKER_PIDFILE
        self.env = _config.env
        self.os = _config.os
        # Below 4 attributes are only for non-sqlite env
        self.DATABASE_USERNAME = ""
        self.DATABASE_PASSWORD = ""
        self.DATABASE_HOST = ""
        self.DATABASE_NAME = ""
        self.DATABASE_FILE = ""
        # This by default is an empty string
        self.CUSTOM_HEADER_IMAGE = ""

        if _config.DATABASE_ENGINE != "sqlite":
            self.DATABASE_USERNAME = _config.DATABASE_USERNAME  # type: ignore
            self.DATABASE_PASSWORSD = \
                _config.DATABASE_PASSWORD   # type: ignore
            self.DATABASE_HOST = _config.DATABASE_HOST  # type: ignore
            self.DATABASE_NAME = _config.DATABASE_NAME  # type: ignore
        else:
            self.DATABASE_FILE = _config.DATABASE_FILE

        if hasattr(_config, 'CUSTOM_HEADER_IMAGE'):
            self.CUSTOM_HEADER_IMAGE = \
                _config.CUSTOM_HEADER_IMAGE  # type: ignore

        if hasattr(_config, 'SUPPORTED_LOCALES'):
            self.SUPPORTED_LOCALES = \
                _config.SUPPORTED_LOCALES  # type: ignore


config = SDConfig()  # type: SDConfig
