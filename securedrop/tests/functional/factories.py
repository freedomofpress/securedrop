from pathlib import Path
import secrets
import shutil
import subprocess
from tests.functional.sd_config_v2 import DEFAULT_SECUREDROP_ROOT, FlaskAppConfig
from tests.functional.sd_config_v2 import SecureDropConfig

from tests.functional.db_session import _get_fake_db_module


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
        SESSION_EXPIRATION_MINUTES: float = 120,
        NOUNS: Path = DEFAULT_SECUREDROP_ROOT / "dictionaries" / "nouns.txt",
        ADJECTIVES: Path = DEFAULT_SECUREDROP_ROOT / "dictionaries" / "adjectives.txt",
    ) -> SecureDropConfig:
        """Create a securedrop config suitable for the unit tests.

        It will automatically create an initialized DB at SECUREDROP_DATA_ROOT/db.sqlite which will
        be set as the DATABASE_FILE.
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
            DATABASE_ENGINE="sqlite",
            JOURNALIST_APP_FLASK_CONFIG_CLS=FlaskAppConfigFactory.create(SESSION_COOKIE_NAME="js"),
            SOURCE_APP_FLASK_CONFIG_CLS=FlaskAppConfigFactory.create(SESSION_COOKIE_NAME="ss"),
            SCRYPT_GPG_PEPPER=_generate_random_token(),
            SCRYPT_ID_PEPPER=_generate_random_token(),
            SCRYPT_PARAMS=dict(N=2 ** 14, r=8, p=1),
            WORKER_PIDFILE="/tmp/securedrop_test_worker.pid",
            RQ_WORKER_NAME="test",
            NOUNS=str(NOUNS),
            ADJECTIVES=str(ADJECTIVES),
            # The next 2 fields must match the GPG fixture
            GPG_KEY_DIR="/tmp/securedrop/keys",
            JOURNALIST_KEY="65A1B5FF195B56353CC63DFFCC40EF1228271441",
        )

        # Delete any previous/existing DB and tnitialize a new one
        database_file.unlink(missing_ok=True)  # type: ignore
        database_file.touch()
        subprocess.check_call(["sqlite3", database_file, ".databases"])
        with _get_fake_db_module(database_uri=config.DATABASE_URI) as initialized_db_module:
            initialized_db_module.create_all()

        # Create the other directories
        Path(config.TEMP_DIR).mkdir(parents=True)
        Path(config.STORE_DIR).mkdir(parents=True)

        # All done
        return config
