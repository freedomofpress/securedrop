from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Dict, List, Optional

FALLBACK_LOCALE = "en_US"

DEFAULT_SECUREDROP_ROOT = Path(__file__).absolute().parent


@dataclass(frozen=True)
class _FlaskAppConfig:
    """Config fields that are common to the Journalist and Source interfaces."""

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
class JournalistInterfaceConfig(_FlaskAppConfig):
    # Additional config for JI Redis sessions
    SESSION_SIGNER_SALT: str = "js_session"
    SESSION_KEY_PREFIX: str = "js_session:"
    SESSION_LIFETIME: int = 2 * 60 * 60
    SESSION_RENEW_COUNT: int = 5


@dataclass(frozen=True)
class SourceInterfaceConfig(_FlaskAppConfig):
    pass


@dataclass(frozen=True)
class SecureDropConfig:
    JOURNALIST_APP_FLASK_CONFIG_CLS: JournalistInterfaceConfig
    SOURCE_APP_FLASK_CONFIG_CLS: SourceInterfaceConfig

    GPG_KEY_DIR: Path
    JOURNALIST_KEY: str
    SCRYPT_GPG_PEPPER: str
    SCRYPT_ID_PEPPER: str
    SCRYPT_PARAMS: Dict[str, int]

    SECUREDROP_DATA_ROOT: Path

    DATABASE_FILE: Path  # Path to the sqlite DB file

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

    env: str = "prod"

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
        return f"sqlite:///{self.DATABASE_FILE}"

    @classmethod
    def get_current(cls) -> "SecureDropConfig":
        global _current_config
        if _current_config is None:
            # Retrieve the config by parsing it from ./config.py
            _current_config = _parse_config_from_file(config_module_name="config")
        return _current_config


_current_config: Optional[SecureDropConfig] = None


def _parse_config_from_file(config_module_name: str) -> SecureDropConfig:
    """Parse the config from a config.py file."""
    config_from_local_file = import_module(config_module_name)

    # Parse the local config; as there are SD instances with very old config files
    # the parsing logic here has to assume some values might be missing, and hence
    # set default values for such config entries
    final_default_locale = getattr(config_from_local_file, "DEFAULT_LOCALE", FALLBACK_LOCALE)
    final_supp_locales = getattr(config_from_local_file, "SUPPORTED_LOCALES", [FALLBACK_LOCALE])
    final_sess_expiration_mins = getattr(config_from_local_file, "SESSION_EXPIRATION_MINUTES", 120)

    final_worker_name = getattr(config_from_local_file, "RQ_WORKER_NAME", "default")

    final_scrypt_params = getattr(config_from_local_file, "SCRYPT_PARAMS", dict(N=2**14, r=8, p=1))

    env = getattr(config_from_local_file, "env", "prod")

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
    parsed_journ_flask_config = JournalistInterfaceConfig(
        SECRET_KEY=journ_flask_config.SECRET_KEY,
        SESSION_COOKIE_NAME=getattr(journ_flask_config, "SESSION_COOKIE_NAME", "js"),
        DEBUG=getattr(journ_flask_config, "DEBUG", False),
        TESTING=getattr(journ_flask_config, "TESTING", False),
        WTF_CSRF_ENABLED=getattr(journ_flask_config, "WTF_CSRF_ENABLED", True),
        MAX_CONTENT_LENGTH=getattr(journ_flask_config, "MAX_CONTENT_LENGTH", 524288000),
        USE_X_SENDFILE=getattr(journ_flask_config, "USE_X_SENDFILE", False),
    )
    source_flask_config = config_from_local_file.SourceInterfaceFlaskConfig
    parsed_source_flask_config = SourceInterfaceConfig(
        SECRET_KEY=source_flask_config.SECRET_KEY,
        SESSION_COOKIE_NAME=getattr(journ_flask_config, "SESSION_COOKIE_NAME", "ss"),
        DEBUG=getattr(journ_flask_config, "DEBUG", False),
        TESTING=getattr(journ_flask_config, "TESTING", False),
        WTF_CSRF_ENABLED=getattr(journ_flask_config, "WTF_CSRF_ENABLED", True),
        MAX_CONTENT_LENGTH=getattr(journ_flask_config, "MAX_CONTENT_LENGTH", 524288000),
        USE_X_SENDFILE=getattr(journ_flask_config, "USE_X_SENDFILE", False),
    )

    return SecureDropConfig(
        env=env,
        JOURNALIST_APP_FLASK_CONFIG_CLS=parsed_journ_flask_config,
        SOURCE_APP_FLASK_CONFIG_CLS=parsed_source_flask_config,
        GPG_KEY_DIR=final_gpg_key_dir,
        JOURNALIST_KEY=config_from_local_file.JOURNALIST_KEY,
        SCRYPT_GPG_PEPPER=config_from_local_file.SCRYPT_GPG_PEPPER,
        SCRYPT_ID_PEPPER=config_from_local_file.SCRYPT_ID_PEPPER,
        SCRYPT_PARAMS=final_scrypt_params,
        SECUREDROP_DATA_ROOT=final_securedrop_data_root,
        SECUREDROP_ROOT=final_securedrop_root,
        DATABASE_FILE=final_db_file,
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
