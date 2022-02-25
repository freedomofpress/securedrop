from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Type


@dataclass()  # TODO: make frozen=True
class SDConfig:
    JOURNALIST_APP_FLASK_CONFIG_CLS: Type
    SOURCE_APP_FLASK_CONFIG_CLS: Type

    DATABASE_ENGINE: str
    DATABASE_FILE: str

    ADJECTIVES: str
    NOUNS: str
    GPG_KEY_DIR: str
    JOURNALIST_KEY: str
    JOURNALIST_TEMPLATES_DIR: str
    SCRYPT_GPG_PEPPER: str
    SCRYPT_ID_PEPPER: str
    SCRYPT_PARAMS: Dict[str, int]
    SECUREDROP_DATA_ROOT: str
    SECUREDROP_ROOT: str
    SOURCE_TEMPLATES_DIR: str
    TEMP_DIR: str
    STORE_DIR: str
    WORKER_PIDFILE: str

    env: str = 'prod'
    RQ_WORKER_NAME: str = 'default'

    DATABASE_USERNAME: Optional[str] = None
    DATABASE_PASSWORD: Optional[str] = None
    DATABASE_HOST: Optional[str] = None
    DATABASE_NAME: Optional[str] = None

    TRANSLATION_DIRS: Optional[str] = None

    SESSION_EXPIRATION_MINUTES: int = 120

    DEFAULT_LOCALE: str = 'en_US'
    SUPPORTED_LOCALES: List[str] = field(default_factory=lambda: ["en_US"])

    @classmethod
    def from_config(cls) -> "SDConfig":
        import config as _config

        kwargs: Dict[str, Any] = {}
        try:
            kwargs['JOURNALIST_APP_FLASK_CONFIG_CLS'] = _config.JournalistInterfaceFlaskConfig
        except AttributeError:
            pass

        try:
            kwargs['SOURCE_APP_FLASK_CONFIG_CLS'] = _config.SourceInterfaceFlaskConfig
        except AttributeError:
            pass

        fields = [
            'DATABASE_ENGINE',
            'DATABASE_FILE',
            'DATABASE_USERNAME',
            'DATABASE_PASSWORD',
            'DATABASE_HOST',
            'DATABASE_NAME',
            'ADJECTIVES',
            'NOUNS',
            'GPG_KEY_DIR',
            'JOURNALIST_KEY',
            'JOURNALIST_TEMPLATES_DIR',
            'SCRYPT_GPG_PEPPER',
            'SCRYPT_ID_PEPPER',
            'SCRYPT_PARAMS',
            'SECUREDROP_DATA_ROOT',
            'SECUREDROP_ROOT',
            'SESSION_EXPIRATION_MINUTES',
            'SOURCE_TEMPLATES_DIR',
            'TEMP_DIR',
            'STORE_DIR',
            'WORKER_PIDFILE',
            'env',
            'DEFAULT_LOCALE',
            'TRANSLATION_DIRS',
            'SUPPORTED_LOCALES',
        ]

        for fieldname in fields:
            try:
                kwargs[fieldname] = getattr(_config, fieldname)
            except AttributeError:
                pass

        if kwargs.get('env') == 'test':
            kwargs['RQ_WORKER_NAME'] = 'test'

        return cls(**kwargs)

    @property
    def translation_dirs(self) -> Path:
        if self.TRANSLATION_DIRS:
            return Path(self.TRANSLATION_DIRS)
        else:
            return Path(self.SECUREDROP_ROOT) / "translations"

    @property
    def supported_locales(self) -> List[str]:
        locales = set(self.SUPPORTED_LOCALES)
        # Make sure the default locale is included
        locales.add(self.DEFAULT_LOCALE)
        supported_locales = list(locales)
        supported_locales.sort()
        return supported_locales

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


config = SDConfig.from_config()  # type: SDConfig
