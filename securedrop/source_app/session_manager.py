from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import sqlalchemy
from flask import session

from sdconfig import config
from source_user import SourceUser, authenticate_source_user, InvalidPassphraseError

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
    """Helper to manage the user's session cookie accessible via flask.session."""

    # The keys in flask.session for the user's passphrase and expiration date
    _SESSION_COOKIE_KEY_FOR_CODENAME = "codename"
    _SESSION_COOKIE_KEY_FOR_EXPIRATION_DATE = "expires"

    @classmethod
    def log_user_in(
        cls,
        db_session: sqlalchemy.orm.Session,
        supplied_passphrase: "DicewarePassphrase"
    ) -> SourceUser:
        # Validate the passphrase; will raise an exception if it is not valid
        source_user = authenticate_source_user(
            db_session=db_session, supplied_passphrase=supplied_passphrase
        )

        # Save the passphrase in the user's session cookie
        session[cls._SESSION_COOKIE_KEY_FOR_CODENAME] = supplied_passphrase

        # Save the session expiration date in the user's session cookie
        session_duration = timedelta(minutes=config.SESSION_EXPIRATION_MINUTES)
        session[cls._SESSION_COOKIE_KEY_FOR_EXPIRATION_DATE] = datetime.now(
            timezone.utc) + session_duration

        return source_user

    @classmethod
    def log_user_out(cls) -> None:
        # Remove session data from the session cookie
        try:
            del session[cls._SESSION_COOKIE_KEY_FOR_CODENAME]
        except KeyError:
            pass

        try:
            del session[cls._SESSION_COOKIE_KEY_FOR_EXPIRATION_DATE]
        except KeyError:
            pass

    @classmethod
    def get_logged_in_user(cls, db_session: sqlalchemy.orm.Session) -> SourceUser:
        # Retrieve the user's passphrase from the Flask session cookie
        try:
            user_passphrase = session[cls._SESSION_COOKIE_KEY_FOR_CODENAME]
            date_session_expires = session[cls._SESSION_COOKIE_KEY_FOR_EXPIRATION_DATE]
        except KeyError:
            cls.log_user_out()
            raise UserNotLoggedIn()

        if datetime.now(timezone.utc) >= date_session_expires:
            cls.log_user_out()
            raise UserSessionExpired()

        # Fetch the user's info
        try:
            source_user = authenticate_source_user(
                db_session=db_session, supplied_passphrase=user_passphrase
            )
        except InvalidPassphraseError:
            # The cookie contains a passphrase that is invalid: happens if the user was deleted
            cls.log_user_out()
            raise UserHasBeenDeleted()

        return source_user

    @classmethod
    def is_user_logged_in(cls, db_session: sqlalchemy.orm.Session) -> bool:
        try:
            cls.get_logged_in_user(db_session)
        except _InvalidUserSession:
            return False

        return True
