from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

# TODO(AD): Should be removed or merged into SecureDropConfig or moved to i18n.py?
FALLBACK_LOCALE = "en_US"

DEFAULT_SECUREDROP_ROOT = Path(__file__).absolute().parent


@dataclass(frozen=True)
class FlaskAppConfig:
    SESSION_COOKIE_NAME: str
    SECRET_KEY: str

    DEBUG: bool
    TESTING: bool
    WTF_CSRF_ENABLED: bool

    # Use MAX_CONTENT_LENGTH to mimic the behavior of Apache's LimitRequestBody
    # in the development environment. See #1714.
    MAX_CONTENT_LENGTH: int

    # This is recommended for performance, and also resolves #369
    USE_X_SENDFILE: bool


@dataclass(frozen=True)
class SecureDropConfig:
    JOURNALIST_APP_FLASK_CONFIG_CLS: FlaskAppConfig
    SOURCE_APP_FLASK_CONFIG_CLS: FlaskAppConfig

    GPG_KEY_DIR: Path
    JOURNALIST_KEY: str
    SCRYPT_GPG_PEPPER: str
    SCRYPT_ID_PEPPER: str
    SCRYPT_PARAMS: Dict[str, int]

    SECUREDROP_DATA_ROOT: Path

    DATABASE_ENGINE: str
    DATABASE_FILE: Path

    # The following fields cannot be None if the DB engine is NOT sqlite
    DATABASE_USERNAME: Optional[str]
    DATABASE_PASSWORD: Optional[str]
    DATABASE_HOST: Optional[str]
    DATABASE_NAME: Optional[str]

    SECUREDROP_ROOT: Path
    STATIC_DIR: Path
    TRANSLATION_DIRS: Path
    SOURCE_TEMPLATES_DIR: Path
    JOURNALIST_TEMPLATES_DIR: Path
    NOUNS: Path
    ADJECTIVES: Path

    DEFAULT_LOCALE: str
    SUPPORTED_LOCALES: List[str]

    SESSION_EXPIRATION_MINUTES: float

    RQ_WORKER_NAME: str

    @property
    def TEMP_DIR(self) -> Path:
        # We use a directory under the SECUREDROP_DATA_ROOT instead of `/tmp` because
        # we need to expose this directory via X-Send-File, and want to minimize the
        # potential for exposing unintended files.
        return self.SECUREDROP_DATA_ROOT / "tmp"

    @property
    def STORE_DIR(self) -> Path:
        return self.SECUREDROP_DATA_ROOT / "store"

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

    @classmethod
    def get_current(cls) -> "SecureDropConfig":
        global _current_config
        if _current_config is None:
            _current_config = _parse_local_config()
        return _current_config


_current_config: Optional[SecureDropConfig] = None


def _parse_local_config() -> SecureDropConfig:
    # Retrieve the config by parsing it from config.py
    import config as config_from_local_file

    # Parse the local config; as there are SD instances with very old config files
    # the parsing logic here has to assume some values might be missing, and hence
    # set default values for such config entries
    final_db_engine = getattr(config_from_local_file, "DATABASE_ENGINE", "sqlite")
    final_db_username = getattr(config_from_local_file, "DATABASE_USERNAME", None)
    final_db_password = getattr(config_from_local_file, "DATABASE_PASSWORD", None)
    final_db_host = getattr(config_from_local_file, "DATABASE_HOST", None)
    final_db_name = getattr(config_from_local_file, "DATABASE_NAME", None)

    final_default_locale = getattr(config_from_local_file, "DEFAULT_LOCALE", "en_US")
    final_supp_locales = getattr(config_from_local_file, "SUPPORTED_LOCALES", ["en_US"])
    final_sess_expiration_mins = getattr(config_from_local_file, "SESSION_EXPIRATION_MINUTES", 120)

    final_worker_name = getattr(config_from_local_file, "RQ_WORKER_NAME", "default")

    final_scrypt_params = getattr(
        config_from_local_file, "SCRYPT_PARAMS", dict(N=2**14, r=8, p=1)
    )

    try:
        final_securedrop_root = Path(config_from_local_file.SECUREDROP_ROOT)
    except AttributeError:
        final_securedrop_root = DEFAULT_SECUREDROP_ROOT

    try:
        final_securedrop_data_root = Path(config_from_local_file.SECUREDROP_DATA_ROOT)
    except AttributeError:
        final_securedrop_data_root = Path("/var/lib/securedrop")

    try:
        final_db_file = Path(config_from_local_file.DATABASE_FILE)
    except AttributeError:
        final_db_file = final_securedrop_data_root / "db.sqlite"

    try:
        final_gpg_key_dir = Path(config_from_local_file.GPG_KEY_DIR)
    except AttributeError:
        final_gpg_key_dir = final_securedrop_data_root / "keys"

    try:
        final_nouns = Path(config_from_local_file.NOUNS)
    except AttributeError:
        final_nouns = final_securedrop_root / "dictionaries" / "nouns.txt"

    try:
        final_adjectives = Path(config_from_local_file.ADJECTIVES)
    except AttributeError:
        final_adjectives = final_securedrop_root / "dictionaries" / "adjectives.txt"

    try:
        final_static_dir = Path(config_from_local_file.STATIC_DIR)  # type: ignore
    except AttributeError:
        final_static_dir = final_securedrop_root / "static"

    try:
        final_transl_dir = Path(config_from_local_file.TRANSLATION_DIRS)  # type: ignore
    except AttributeError:
        final_transl_dir = final_securedrop_root / "translations"

    try:
        final_source_tmpl_dir = Path(config_from_local_file.SOURCE_TEMPLATES_DIR)
    except AttributeError:
        final_source_tmpl_dir = final_securedrop_root / "source_templates"

    try:
        final_journ_tmpl_dir = Path(config_from_local_file.JOURNALIST_TEMPLATES_DIR)
    except AttributeError:
        final_journ_tmpl_dir = final_securedrop_root / "journalist_templates"

    # Parse the Flask configurations
    journ_flask_config = config_from_local_file.JournalistInterfaceFlaskConfig
    parsed_journ_flask_config = FlaskAppConfig(
        SESSION_COOKIE_NAME=journ_flask_config.SESSION_COOKIE_NAME,
        SECRET_KEY=journ_flask_config.SECRET_KEY,
        DEBUG=getattr(journ_flask_config, "DEBUG", False),
        TESTING=getattr(journ_flask_config, "TESTING", False),
        WTF_CSRF_ENABLED=getattr(journ_flask_config, "WTF_CSRF_ENABLED", True),
        MAX_CONTENT_LENGTH=getattr(journ_flask_config, "MAX_CONTENT_LENGTH", 524288000),
        USE_X_SENDFILE=getattr(journ_flask_config, "USE_X_SENDFILE", False),
    )
    source_flask_config = config_from_local_file.SourceInterfaceFlaskConfig
    parsed_source_flask_config = FlaskAppConfig(
        SESSION_COOKIE_NAME=source_flask_config.SESSION_COOKIE_NAME,
        SECRET_KEY=source_flask_config.SECRET_KEY,
        DEBUG=getattr(journ_flask_config, "DEBUG", False),
        TESTING=getattr(journ_flask_config, "TESTING", False),
        WTF_CSRF_ENABLED=getattr(journ_flask_config, "WTF_CSRF_ENABLED", True),
        MAX_CONTENT_LENGTH=getattr(journ_flask_config, "MAX_CONTENT_LENGTH", 524288000),
        USE_X_SENDFILE=getattr(journ_flask_config, "USE_X_SENDFILE", False),
    )

    return SecureDropConfig(
        JOURNALIST_APP_FLASK_CONFIG_CLS=parsed_journ_flask_config,
        SOURCE_APP_FLASK_CONFIG_CLS=parsed_source_flask_config,
        GPG_KEY_DIR=final_gpg_key_dir,
        JOURNALIST_KEY=config_from_local_file.JOURNALIST_KEY,
        SCRYPT_GPG_PEPPER=config_from_local_file.SCRYPT_GPG_PEPPER,
        SCRYPT_ID_PEPPER=config_from_local_file.SCRYPT_ID_PEPPER,
        SCRYPT_PARAMS=final_scrypt_params,
        SECUREDROP_DATA_ROOT=final_securedrop_data_root,
        SECUREDROP_ROOT=final_securedrop_root,
        DATABASE_ENGINE=final_db_engine,
        DATABASE_FILE=final_db_file,
        DATABASE_USERNAME=final_db_username,
        DATABASE_PASSWORD=final_db_password,
        DATABASE_HOST=final_db_host,
        DATABASE_NAME=final_db_name,
        STATIC_DIR=final_static_dir,
        TRANSLATION_DIRS=final_transl_dir,
        SOURCE_TEMPLATES_DIR=final_source_tmpl_dir,
        JOURNALIST_TEMPLATES_DIR=final_journ_tmpl_dir,
        NOUNS=final_nouns,
        ADJECTIVES=final_adjectives,
        DEFAULT_LOCALE=final_default_locale,
        SUPPORTED_LOCALES=final_supp_locales,
        SESSION_EXPIRATION_MINUTES=final_sess_expiration_mins,
        RQ_WORKER_NAME=final_worker_name,
    )
