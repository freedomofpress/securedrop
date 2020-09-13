from typing import Dict
from typing import Optional

from typing import Type

import config as _config


class SDConfig:
    def __init__(self) -> None:
        self.JOURNALIST_APP_FLASK_CONFIG_CLS = \
            _config.JournalistInterfaceFlaskConfig  # type: Type

        self.SOURCE_APP_FLASK_CONFIG_CLS = \
            _config.SourceInterfaceFlaskConfig  # type: Type

        self.DATABASE_ENGINE = _config.DATABASE_ENGINE  # type: str
        self.DATABASE_FILE = _config.DATABASE_FILE  # type: str

        self.DATABASE_USERNAME = getattr(_config, "DATABASE_USERNAME", None)  # type: Optional[str]
        self.DATABASE_PASSWORD = getattr(_config, "DATABASE_PASSWORD", None)  # type: Optional[str]
        self.DATABASE_HOST = getattr(_config, "DATABASE_HOST", None)  # type: Optional[str]
        self.DATABASE_NAME = getattr(_config, "DATABASE_NAME", None)  # type: Optional[str]

        self.ADJECTIVES = _config.ADJECTIVES  # type: str
        self.NOUNS = _config.NOUNS  # type: str
        self.WORD_LIST = _config.WORD_LIST  # type: str

        self.DEFAULT_LOCALE = _config.DEFAULT_LOCALE  # type: str
        self.SUPPORTED_LOCALES = getattr(_config, "SUPPORTED_LOCALES", None)  # type: Optional[str]

        self.GPG_KEY_DIR = _config.GPG_KEY_DIR  # type: str

        self.JOURNALIST_KEY = _config.JOURNALIST_KEY  # type: str
        self.JOURNALIST_TEMPLATES_DIR = _config.JOURNALIST_TEMPLATES_DIR  # type: str

        self.SCRYPT_GPG_PEPPER = _config.SCRYPT_GPG_PEPPER  # type: str
        self.SCRYPT_ID_PEPPER = _config.SCRYPT_ID_PEPPER  # type: str
        self.SCRYPT_PARAMS = _config.SCRYPT_PARAMS  # type: Dict[str, int]

        self.SECUREDROP_DATA_ROOT = _config.SECUREDROP_DATA_ROOT  # type: str
        self.SECUREDROP_ROOT = _config.SECUREDROP_ROOT  # type: str

        self.SESSION_EXPIRATION_MINUTES = _config.SESSION_EXPIRATION_MINUTES  # type: int

        self.SOURCE_TEMPLATES_DIR = _config.SOURCE_TEMPLATES_DIR  # type: str
        self.TEMP_DIR = _config.TEMP_DIR  # type: str
        self.STORE_DIR = _config.STORE_DIR  # type: str
        self.TRANSLATION_DIRS = getattr(_config, "TRANSLATION_DIRS", None)  # type: Optional[str]

        self.WORKER_PIDFILE = _config.WORKER_PIDFILE  # type: str

        if _config.env == 'test':
            self.RQ_WORKER_NAME = 'test'  # type: str
        else:
            self.RQ_WORKER_NAME = 'default'

    @property
    def DATABASE_URI(self) -> str:
        if config.DATABASE_ENGINE == "sqlite":
            db_uri = (config.DATABASE_ENGINE + ":///" +
                      config.DATABASE_FILE)
        else:
            if config.DATABASE_USERNAME is None:
                raise RuntimeError("Missing DATABASE_USERNAME entry from config.py")
            if config.DATABASE_PASSWORD is None:
                raise RuntimeError("Missing DATABASE_PASSWORD entry from config.py")
            if config.DATABASE_HOST is None:
                raise RuntimeError("Missing DATABASE_HOST entry from config.py")
            if config.DATABASE_NAME is None:
                raise RuntimeError("Missing DATABASE_NAME entry from config.py")

            db_uri = (
                config.DATABASE_ENGINE + '://' +
                config.DATABASE_USERNAME + ':' +
                config.DATABASE_PASSWORD + '@' +
                config.DATABASE_HOST + '/' +
                config.DATABASE_NAME
            )
        return db_uri


config = SDConfig()  # type: SDConfig
