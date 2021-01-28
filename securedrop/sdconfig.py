from pathlib import Path
from typing import Dict
from typing import Optional

from typing import Type

import config as _config
from typing import Set


class SDConfig:
    def __init__(self) -> None:
        try:
            self.JOURNALIST_APP_FLASK_CONFIG_CLS = (
                _config.JournalistInterfaceFlaskConfig
            )  # type: Type
        except AttributeError:
            pass

        try:
            self.SOURCE_APP_FLASK_CONFIG_CLS = _config.SourceInterfaceFlaskConfig  # type: Type
        except AttributeError:
            pass

        try:
            self.DATABASE_ENGINE = _config.DATABASE_ENGINE  # type: str
        except AttributeError:
            pass

        try:
            self.DATABASE_FILE = _config.DATABASE_FILE  # type: str
        except AttributeError:
            pass

        self.DATABASE_USERNAME = getattr(_config, "DATABASE_USERNAME", None)  # type: Optional[str]
        self.DATABASE_PASSWORD = getattr(_config, "DATABASE_PASSWORD", None)  # type: Optional[str]
        self.DATABASE_HOST = getattr(_config, "DATABASE_HOST", None)  # type: Optional[str]
        self.DATABASE_NAME = getattr(_config, "DATABASE_NAME", None)  # type: Optional[str]

        try:
            self.ADJECTIVES = _config.ADJECTIVES  # type: str
        except AttributeError:
            pass

        try:
            self.NOUNS = _config.NOUNS  # type: str
        except AttributeError:
            pass

        try:
            self.GPG_KEY_DIR = _config.GPG_KEY_DIR  # type: str
        except AttributeError:
            pass

        try:
            self.JOURNALIST_KEY = _config.JOURNALIST_KEY  # type: str
        except AttributeError:
            pass

        try:
            self.JOURNALIST_TEMPLATES_DIR = _config.JOURNALIST_TEMPLATES_DIR  # type: str
        except AttributeError:
            pass

        try:
            self.SCRYPT_GPG_PEPPER = _config.SCRYPT_GPG_PEPPER  # type: str
        except AttributeError:
            pass

        try:
            self.SCRYPT_ID_PEPPER = _config.SCRYPT_ID_PEPPER  # type: str
        except AttributeError:
            pass

        try:
            self.SCRYPT_PARAMS = _config.SCRYPT_PARAMS  # type: Dict[str, int]
        except AttributeError:
            pass

        try:
            self.SECUREDROP_DATA_ROOT = _config.SECUREDROP_DATA_ROOT  # type: str
        except AttributeError:
            pass

        try:
            self.SECUREDROP_ROOT = _config.SECUREDROP_ROOT  # type: str
        except AttributeError:
            pass

        try:
            self.SESSION_EXPIRATION_MINUTES = _config.SESSION_EXPIRATION_MINUTES  # type: int
        except AttributeError:
            pass

        try:
            self.SOURCE_TEMPLATES_DIR = _config.SOURCE_TEMPLATES_DIR  # type: str
        except AttributeError:
            pass

        try:
            self.TEMP_DIR = _config.TEMP_DIR  # type: str
        except AttributeError:
            pass

        try:
            self.STORE_DIR = _config.STORE_DIR  # type: str
        except AttributeError:
            pass

        try:
            self.WORKER_PIDFILE = _config.WORKER_PIDFILE  # type: str
        except AttributeError:
            pass

        self.env = getattr(_config, 'env', 'prod')  # type: str
        if self.env == 'test':
            self.RQ_WORKER_NAME = 'test'  # type: str
        else:
            self.RQ_WORKER_NAME = 'default'

        # Config entries used by i18n.py
        # Use en_US as the default locale if the key is not defined in _config
        self.DEFAULT_LOCALE = getattr(
            _config, "DEFAULT_LOCALE", "en_US"
        )  # type: str
        supported_locales = set(getattr(
            _config, "SUPPORTED_LOCALES", [self.DEFAULT_LOCALE]
        ))  # type: Set[str]
        supported_locales.add(self.DEFAULT_LOCALE)
        self.SUPPORTED_LOCALES = sorted(list(supported_locales))

        translation_dirs_in_conf = getattr(_config, "TRANSLATION_DIRS", None)  # type: Optional[str]
        if translation_dirs_in_conf:
            self.TRANSLATION_DIRS = Path(translation_dirs_in_conf)  # type: Path
        else:
            try:
                self.TRANSLATION_DIRS = Path(_config.SECUREDROP_ROOT) / "translations"
            except AttributeError:
                pass

    @property
    def DATABASE_URI(self) -> str:
        if self.DATABASE_ENGINE == "sqlite":
            db_uri = (self.DATABASE_ENGINE + ":///" +
                      self.DATABASE_FILE)
        else:
            if self.DATABASE_USERNAME is None:
                raise RuntimeError("Missing DATABASE_USERNAME entry from config.py")
            if self.DATABASE_PASSWORD is None:
                raise RuntimeError("Missing DATABASE_PASSWORD entry from config.py")
            if self.DATABASE_HOST is None:
                raise RuntimeError("Missing DATABASE_HOST entry from config.py")
            if self.DATABASE_NAME is None:
                raise RuntimeError("Missing DATABASE_NAME entry from config.py")

            db_uri = (
                self.DATABASE_ENGINE + '://' +
                self.DATABASE_USERNAME + ':' +
                self.DATABASE_PASSWORD + '@' +
                self.DATABASE_HOST + '/' +
                self.DATABASE_NAME
            )
        return db_uri


config = SDConfig()  # type: SDConfig
