from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(frozen=True)
class FlaskAppConfig:
    SESSION_COOKIE_NAME: str
    SECRET_KEY: str

    DEBUG: bool = False
    TESTING: bool = False
    WTF_CSRF_ENABLED: bool = True

    # Use MAX_CONTENT_LENGTH to mimic the behavior of Apache's LimitRequestBody
    # in the development environment. See #1714.
    MAX_CONTENT_LENGTH: int = 524288000

    # This is recommended for performance, and also resolves #369
    USE_X_SENDFILE: bool = True

    # additional config for JI Redis sessions
    SESSION_SIGNER_SALT: str = "js_session"
    SESSION_KEY_PREFIX: str = "js_session:"
    SESSION_LIFETIME: int = 2 * 60 * 60
    SESSION_RENEW_COUNT: int = 5


DEFAULT_SECUREDROP_ROOT = Path(__file__).absolute().parent.parent.parent


# TODO(AD): This mirrors the field in an SDConfig; it is intended to eventually replace it
@dataclass(frozen=True)
class SecureDropConfig:
    JOURNALIST_APP_FLASK_CONFIG_CLS: FlaskAppConfig
    SOURCE_APP_FLASK_CONFIG_CLS: FlaskAppConfig

    GPG_KEY_DIR: str
    JOURNALIST_KEY: str
    SCRYPT_GPG_PEPPER: str
    SCRYPT_ID_PEPPER: str
    SCRYPT_PARAMS: Dict[str, int]

    SECUREDROP_DATA_ROOT: str

    DATABASE_ENGINE: str
    DATABASE_FILE: str

    # The following fields are required if the DB engine is NOT sqlite
    DATABASE_USERNAME: Optional[str] = None
    DATABASE_PASSWORD: Optional[str] = None
    DATABASE_HOST: Optional[str] = None
    DATABASE_NAME: Optional[str] = None

    SECUREDROP_ROOT: str = str(DEFAULT_SECUREDROP_ROOT)
    TRANSLATION_DIRS: Path = DEFAULT_SECUREDROP_ROOT / "translations"
    SOURCE_TEMPLATES_DIR: str = str(DEFAULT_SECUREDROP_ROOT / "source_templates")
    JOURNALIST_TEMPLATES_DIR: str = str(DEFAULT_SECUREDROP_ROOT / "journalist_templates")
    NOUNS: str = str(DEFAULT_SECUREDROP_ROOT / "dictionaries" / "nouns.txt")
    ADJECTIVES: str = str(DEFAULT_SECUREDROP_ROOT / "dictionaries" / "adjectives.txt")

    DEFAULT_LOCALE: str = "en_US"
    SUPPORTED_LOCALES: List[str] = field(default_factory=lambda: ["en_US"])

    SESSION_EXPIRATION_MINUTES: float = 120

    WORKER_PIDFILE: str = "/tmp/securedrop_worker.pid"
    RQ_WORKER_NAME: str = "default"

    @property
    def TEMP_DIR(self) -> str:
        # We use a directory under the SECUREDROP_DATA_ROOT instead of `/tmp` because
        # we need to expose this directory via X-Send-File, and want to minimize the
        # potential for exposing unintended files.
        return str(Path(self.SECUREDROP_DATA_ROOT) / "tmp")

    @property
    def STORE_DIR(self) -> str:
        return str(Path(self.SECUREDROP_DATA_ROOT) / "store")

    @property
    def DATABASE_URI(self) -> str:
        if self.DATABASE_ENGINE == "sqlite":
            db_uri = f"{self.DATABASE_ENGINE}:///{self.DATABASE_FILE}"

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
                self.DATABASE_ENGINE
                + "://"
                + self.DATABASE_USERNAME
                + ":"
                + self.DATABASE_PASSWORD
                + "@"
                + self.DATABASE_HOST
                + "/"
                + self.DATABASE_NAME
            )
        return db_uri
