import binascii
import os

from flask import session
from werkzeug.contrib.cache import SimpleCache

from sdconfig import config
from source_user import SourceUser


class _InvalidUserSession(Exception):
    pass


class UserNotLoggedIn(_InvalidUserSession):
    pass


class UserSessionExpired(_InvalidUserSession):
    pass


class UserHasBeenDeleted(_InvalidUserSession):
    pass


class SessionManager:
    _SESSION_ID_LENGTH = 32
    _CACHE = SimpleCache()  # A mapping of session_id -> SourceUser
    _KEY_FOR_SESSION_ID = "source_user_session_id"

    @classmethod
    def log_user_in(cls, user: SourceUser) -> None:
        # Generate a session ID for this user
        user_session_id = binascii.hexlify(os.urandom(cls._SESSION_ID_LENGTH))

        # Store the user's information
        cls._CACHE.set(
            key=user_session_id, value=user, timeout=config.SESSION_EXPIRATION_MINUTES * 60
        )

        # Save the user's session ID in the Flask session cookie in the user's browser
        session[cls._KEY_FOR_SESSION_ID] = user_session_id

    @classmethod
    def log_user_out(cls) -> None:
        try:
            user_session_id = session[cls._KEY_FOR_SESSION_ID]
            cls._CACHE.delete(user_session_id)
        except KeyError:
            pass

    @classmethod
    def get_logged_in_user(cls) -> SourceUser:
        # Retrieve the user's session ID from the Flask session cookie
        try:
            user_session_id = session[cls._KEY_FOR_SESSION_ID]
        except KeyError:
            raise UserNotLoggedIn()

        # Lookup the user's info
        user_info = cls._CACHE.get(user_session_id)
        if not user_info:
            del session[cls._KEY_FOR_SESSION_ID]
            raise UserSessionExpired()

        # Ensure the user hasn't been deleted since the last request
        if user_info.get_db_record() is None or user_info.get_db_record().deleted_at:
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
    def log_all_users_out(cls) -> None:
        """Expire the session of all currently-logged-in users.

        Should only be used by the unit tests."""
        cls._CACHE.clear()
