from typing import TYPE_CHECKING

from flask import session
from werkzeug.contrib.cache import SimpleCache

from sdconfig import config
from source_user import SourceUser

if TYPE_CHECKING:
    from passphrases import DicewarePassphrase


class _InvalidUserSession(Exception):
    pass


class UserNotLoggedIn(_InvalidUserSession):
    pass


class UserSessionExpired(_InvalidUserSession):
    pass


class UserHasBeenDeleted(_InvalidUserSession):
    pass


class SessionManager:
    _CACHE = SimpleCache()  # A mapping of passphrase -> SourceUser
    _KEY_IN_SESSION_COOKIE = "codename"  # The key in flask.session for the user's passphrase

    @classmethod
    def log_user_in(cls, user: SourceUser, user_passphrase: "DicewarePassphrase") -> None:
        # Save the passphrase in the user's session cookie
        session[cls._KEY_IN_SESSION_COOKIE] = user_passphrase

        # Store the user's information
        cls._CACHE.set(
            key=user_passphrase, value=user, timeout=config.SESSION_EXPIRATION_MINUTES * 60
        )

    @classmethod
    def log_user_out(cls) -> None:
        try:
            # Retrieve the passphrase from the session cookie and delete the user's info
            user_passphrase = session[cls._KEY_IN_SESSION_COOKIE]
            cls._CACHE.delete(user_passphrase)
            # Remove passphrase from the session cookie
            del session[cls._KEY_IN_SESSION_COOKIE]
        except KeyError:
            pass

    @classmethod
    def get_logged_in_user(cls) -> SourceUser:
        # Retrieve the user's passphrase from the Flask session cookie
        try:
            user_passphrase = session[cls._KEY_IN_SESSION_COOKIE]
        except KeyError:
            cls.log_user_out()
            raise UserNotLoggedIn()

        # Lookup the user's info
        user_info = cls._CACHE.get(user_passphrase)
        if not user_info:
            cls.log_user_out()
            raise UserSessionExpired()

        # Ensure the user hasn't been deleted since the last request
        if user_info.get_db_record() is None or user_info.get_db_record().deleted_at:
            cls.log_user_out()
            raise UserHasBeenDeleted(
                "Source user {} has been deleted".format(user_info.db_record_id)
            )

        return user_info

    @classmethod
    def is_user_logged_in(cls) -> bool:
        try:
            cls.get_logged_in_user()
        except _InvalidUserSession:
            return False

        return True

    @classmethod
    def expire_all_user_sessions(cls) -> None:
        """Expire the session of all currently-logged-in users.

        Should only be used by the unit tests."""
        cls._CACHE.clear()
