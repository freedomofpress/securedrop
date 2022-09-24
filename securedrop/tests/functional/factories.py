import secrets
import shutil
from pathlib import Path
from typing import List, Optional

from tests.functional.db_session import _get_fake_db_module
from tests.functional.sd_config_v2 import DEFAULT_SECUREDROP_ROOT, FlaskAppConfig, SecureDropConfig
from tests.utils.db_helper import reset_database


def _generate_random_token() -> str:
    return secrets.token_hex(32)


class FlaskAppConfigFactory:
    @staticmethod
    def create(SESSION_COOKIE_NAME: str) -> FlaskAppConfig:
        """Create a Flask app config suitable for the unit tests."""
        return FlaskAppConfig(
            SESSION_COOKIE_NAME=SESSION_COOKIE_NAME,
            SECRET_KEY=_generate_random_token(),
            TESTING=True,
            USE_X_SENDFILE=False,
            # Disable CSRF checks to make writing tests easier
            WTF_CSRF_ENABLED=False,
        )


class SecureDropConfigFactory:
    @staticmethod
    def create(
        SECUREDROP_DATA_ROOT: Path,
        GPG_KEY_DIR: Path,
        JOURNALIST_KEY: str,
        RQ_WORKER_NAME: str,
        SESSION_EXPIRATION_MINUTES: float = 120,
        NOUNS: Path = DEFAULT_SECUREDROP_ROOT / "dictionaries" / "nouns.txt",
        ADJECTIVES: Path = DEFAULT_SECUREDROP_ROOT / "dictionaries" / "adjectives.txt",
        SUPPORTED_LOCALES: Optional[List[str]] = None,
        DEFAULT_LOCALE: str = "en_US",
        TRANSLATION_DIRS: Path = DEFAULT_SECUREDROP_ROOT / "translations",
    ) -> SecureDropConfig:
        """Create a securedrop config suitable for the unit tests.

        It will erase any existing file within SECUREDROP_DATA_ROOT and then create an initialized
        DB at SECUREDROP_DATA_ROOT/db.sqlite which will be set as the DATABASE_FILE.
        """
        # Clear the data root directory
        if SECUREDROP_DATA_ROOT.exists():
            shutil.rmtree(SECUREDROP_DATA_ROOT)
        SECUREDROP_DATA_ROOT.mkdir(parents=True)
        database_file = SECUREDROP_DATA_ROOT / "db.sqlite"

        config = SecureDropConfig(
            SESSION_EXPIRATION_MINUTES=SESSION_EXPIRATION_MINUTES,
            SECUREDROP_DATA_ROOT=str(SECUREDROP_DATA_ROOT),
            DATABASE_FILE=str(database_file),
            SECUREDROP_ROOT=DEFAULT_SECUREDROP_ROOT,
            DATABASE_ENGINE="sqlite",
            JOURNALIST_APP_FLASK_CONFIG_CLS=FlaskAppConfigFactory.create(SESSION_COOKIE_NAME="js"),
            SOURCE_APP_FLASK_CONFIG_CLS=FlaskAppConfigFactory.create(SESSION_COOKIE_NAME="ss"),
            SCRYPT_GPG_PEPPER=_generate_random_token(),
            SCRYPT_ID_PEPPER=_generate_random_token(),
            SCRYPT_PARAMS=dict(N=2**14, r=8, p=1),
            WORKER_PIDFILE="/tmp/securedrop_test_worker.pid",
            NOUNS=str(NOUNS),
            ADJECTIVES=str(ADJECTIVES),
            RQ_WORKER_NAME=RQ_WORKER_NAME,
            GPG_KEY_DIR=str(GPG_KEY_DIR),
            JOURNALIST_KEY=JOURNALIST_KEY,
            SUPPORTED_LOCALES=SUPPORTED_LOCALES if SUPPORTED_LOCALES is not None else ["en_US"],
            TRANSLATION_DIRS=TRANSLATION_DIRS,
            SOURCE_TEMPLATES_DIR=DEFAULT_SECUREDROP_ROOT / "source_templates",
            JOURNALIST_TEMPLATES_DIR=DEFAULT_SECUREDROP_ROOT / "journalist_templates",
            DEFAULT_LOCALE=DEFAULT_LOCALE,
        )

        # Delete any previous/existing DB and initialize a new one
        reset_database(database_file)
        with _get_fake_db_module(database_uri=config.DATABASE_URI) as initialized_db_module:
            initialized_db_module.create_all()

        # Create the other directories
        Path(config.TEMP_DIR).mkdir(parents=True)
        Path(config.STORE_DIR).mkdir(parents=True)

        # All done
        return config
