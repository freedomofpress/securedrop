import datetime

import pytest

from db import db
from passphrases import PassphraseGenerator
from source_app.session_manager import (
    SessionManager,
    UserNotLoggedIn,
    UserSessionExpired,
    UserHasBeenDeleted,
)
from source_user import create_source_user


class TestSessionManager:
    def test_log_user_in(self, source_app):
        # Given a source user
        passphrase = PassphraseGenerator.get_default().generate_passphrase()
        source_user = create_source_user(
            db_session=db.session,
            source_passphrase=passphrase,
            source_app_crypto_util=source_app.crypto_util,
            source_app_storage=source_app.storage,
        )

        with source_app.test_request_context():
            # When they log in, it succeeds
            SessionManager.log_user_in(source_user, passphrase)

            # And the SessionManager returns them as the current user
            assert SessionManager.is_user_logged_in()
            logged_in_user = SessionManager.get_logged_in_user()
            assert logged_in_user.db_record_id == source_user.db_record_id

    def test_log_user_out(self, source_app):
        # Given a source user
        passphrase = PassphraseGenerator.get_default().generate_passphrase()
        source_user = create_source_user(
            db_session=db.session,
            source_passphrase=passphrase,
            source_app_crypto_util=source_app.crypto_util,
            source_app_storage=source_app.storage,
        )

        with source_app.test_request_context():
            # Who previously logged in
            SessionManager.log_user_in(source_user, passphrase)

            # When they log out, it succeeds
            SessionManager.log_user_out()

            # And the SessionManager no longer returns a current user
            assert not SessionManager.is_user_logged_in()
            with pytest.raises(UserNotLoggedIn):
                SessionManager.get_logged_in_user()

    def test_get_logged_in_user_but_session_expired(self, source_app):
        # Given a source user
        passphrase = PassphraseGenerator.get_default().generate_passphrase()
        source_user = create_source_user(
            db_session=db.session,
            source_passphrase=passphrase,
            source_app_crypto_util=source_app.crypto_util,
            source_app_storage=source_app.storage,
        )

        with source_app.test_request_context():
            # Who previously logged in
            SessionManager.log_user_in(source_user, passphrase)
            # But since then their session expired
            SessionManager.expire_all_user_sessions()

            # When querying the current user from the SessionManager, it fails with the right error
            with pytest.raises(UserSessionExpired):
                SessionManager.get_logged_in_user()

    def test_get_logged_in_user_but_user_deleted(self, source_app):
        # Given a source user
        passphrase = PassphraseGenerator.get_default().generate_passphrase()
        source_user = create_source_user(
            db_session=db.session,
            source_passphrase=passphrase,
            source_app_crypto_util=source_app.crypto_util,
            source_app_storage=source_app.storage,
        )

        with source_app.test_request_context():
            # Who previously logged in
            SessionManager.log_user_in(source_user, passphrase)
            # But since then their account was deleted
            source_in_db = source_user.get_db_record()
            source_in_db.deleted_at = datetime.datetime.utcnow()
            db.session.commit()

            # When querying the current user from the SessionManager, it fails with the right error
            with pytest.raises(UserHasBeenDeleted):
                SessionManager.get_logged_in_user()
