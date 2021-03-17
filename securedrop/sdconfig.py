from pathlib import Path
from typing import Dict
from typing import Optional

from typing import Type

import config as _config
from typing import Set

from signal_protocol.curve import KeyPair
from signal_protocol.sealed_sender import ServerCertificate


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

        # Server cert generation for sealed sender.
        # In a production deployment, this would be generated along with the other
        # app code bits at install time (e.g. the Flask secret key)
        SERVER_ID = 666

        # TEMP: HARDCODED for demo purposes
        # trust_root = KeyPair.generate()
        # trust_root.private_key().serialize()
        trust_root_priv = b'\xd8?\xb8\x8a\x01\xc8j\xe3@\x89F\xa3c\x8cL\xf7\xfb(\xdc%\xfc\xcb,T\xd5\xcb\x02C[\xf7\xf3H'
        # trust_root.public_key().serialize()
        trust_root_pub = b"\x05\xa0\x0f\xdfy\xea7\x8f\xc8M\r'\xf5f=\xa3\xdd\xc4p\xee\xb1Qt\x14N\xa0\xbc\xe84\xa8\x1d\xaa:"
        trust_root = KeyPair.from_public_and_private(trust_root_pub, trust_root_priv)

        # server_key = KeyPair.generate()
        # server_key.private_key().serialize()
        server_key_priv = b'\xe0\xe6\x13\x92\x11\xc7<\x1c\xb2\x93i\xdb\xd0\x0cL\xe2\xaa\xdf\xc1\xe5\xe08{\x8fO\xea;\x8b4?\xb7S'
        # server_key.public_key().serialize()
        server_key_pub = b'\x05\x1e-\xe1\x05\xea2]\xe98\x04\xd9\xf4\r\x1dE\xde\xf2\x8c\x03\x08+\xa0A\x08\xa0\xf75\x1e\xa0\x99{\x00'
        server_key = KeyPair.from_public_and_private(server_key_pub, server_key_priv)

        self.trust_root = trust_root
        self.server_key = server_key

        self.server_cert = ServerCertificate(
            SERVER_ID, server_key.public_key(), trust_root.private_key()
        )

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
