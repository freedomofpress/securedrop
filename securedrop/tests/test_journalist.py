# flake8: noqa: E741
import base64
import binascii
import io
import os
import random
import time
import zipfile
from base64 import b64decode
from io import BytesIO
from pathlib import Path
from typing import Tuple
from unittest.mock import call, patch

import journalist_app as journalist_app_module
import pytest
from db import db
from encryption import EncryptionManager, GpgKeyNotFoundError
from flaky import flaky
from flask import escape, g, url_for
from flask_babel import gettext, ngettext
from journalist_app.sessions import session
from journalist_app.utils import mark_seen
from models import (
    InstanceConfig,
    InvalidPasswordLength,
    InvalidUsernameException,
    Journalist,
    JournalistLoginAttempt,
    Reply,
    SeenFile,
    SeenMessage,
    SeenReply,
    Source,
    Submission,
)
from passphrases import PassphraseGenerator
from source_user import create_source_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.sql.expression import func
from store import Storage
from tests import utils
from tests.factories.configs_factories import SecureDropConfigFactory
from tests.functional.db_session import get_database_session
from tests.utils import login_journalist
from tests.utils.i18n import (
    get_plural_tests,
    get_test_locales,
    language_tag,
    page_language,
    xfail_untranslated_messages,
)
from tests.utils.instrument import InstrumentedApp
from two_factor import TOTP

# Smugly seed the RNG for deterministic testing
random.seed(r"¯\_(ツ)_/¯")

VALID_PASSWORD = "correct horse battery staple generic passphrase hooray"
VALID_PASSWORD_2 = "another correct horse battery staple generic passphrase"


def test_user_with_whitespace_in_username_can_login(journalist_app):
    # Create a user with whitespace at the end of the username
    with get_database_session(journalist_app.config["SQLALCHEMY_DATABASE_URI"]) as db_session:
        username_with_whitespace = "journalist "
        password = PassphraseGenerator.get_default().generate_passphrase()
        user = Journalist(
            username=username_with_whitespace,
            password=password,
        )
        db_session.add(user)
        db_session.commit()
        otp_secret = user.otp_secret

    # Verify that user is able to login successfully
    with journalist_app.test_client() as app:
        login_journalist(app, username_with_whitespace, password, otp_secret)


def test_reply_error_logging(journalist_app, test_journo, test_source):
    exception_class = StaleDataError
    exception_msg = "Potentially sensitive content!"

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )
        with patch.object(journalist_app.logger, "error") as mocked_error_logger:
            with patch.object(db.session, "commit", side_effect=exception_class(exception_msg)):
                resp = app.post(
                    url_for("main.reply"),
                    data={
                        "filesystem_id": test_source["filesystem_id"],
                        "message": "_",
                    },
                    follow_redirects=True,
                )
                assert resp.status_code == 200

    # Notice the "potentially sensitive" exception_msg is not present in
    # the log event.
    mocked_error_logger.assert_called_once_with(
        "Reply from '{}' (ID {}) failed: {}!".format(
            test_journo["username"], test_journo["id"], exception_class
        )
    )


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_reply_error_flashed_message(config, journalist_app, test_journo, test_source, locale):
    exception_class = StaleDataError

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )

        with InstrumentedApp(app) as ins:
            with patch.object(db.session, "commit", side_effect=exception_class()):
                resp = app.post(
                    url_for("main.reply", l=locale),
                    data={
                        "filesystem_id": test_source["filesystem_id"],
                        "message": "_",
                    },
                    follow_redirects=True,
                )

                assert page_language(resp.data) == language_tag(locale)
                msgids = ["An unexpected error occurred! Please inform your admin."]
                with xfail_untranslated_messages(config, locale, msgids):
                    ins.assert_message_flashed(gettext(msgids[0]), "error")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_empty_replies_are_rejected(config, journalist_app, test_journo, test_source, locale):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )
        resp = app.post(
            url_for("main.reply", l=locale),
            data={"filesystem_id": test_source["filesystem_id"], "message": ""},
            follow_redirects=True,
        )

        assert page_language(resp.data) == language_tag(locale)
        msgids = ["You cannot send an empty reply."]
        with xfail_untranslated_messages(config, locale, msgids):
            assert gettext(msgids[0]) in resp.data.decode("utf-8")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_nonempty_replies_are_accepted(config, journalist_app, test_journo, test_source, locale):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )
        resp = app.post(
            url_for("main.reply", l=locale),
            data={"filesystem_id": test_source["filesystem_id"], "message": "_"},
            follow_redirects=True,
        )

        assert page_language(resp.data) == language_tag(locale)
        msgids = ["You cannot send an empty reply."]
        with xfail_untranslated_messages(config, locale, msgids):
            assert gettext(msgids[0]) not in resp.data.decode("utf-8")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_successful_reply_marked_as_seen_by_sender(
    config, journalist_app, test_journo, test_source, locale
):
    with journalist_app.test_client() as app:
        journo = test_journo["journalist"]
        login_journalist(app, journo.username, test_journo["password"], test_journo["otp_secret"])

        seen_reply = SeenReply.query.filter_by(journalist_id=journo.id).one_or_none()
        assert not seen_reply

        resp = app.post(
            url_for("main.reply", l=locale),
            data={"filesystem_id": test_source["filesystem_id"], "message": "_"},
            follow_redirects=True,
        )

        assert page_language(resp.data) == language_tag(locale)
        msgids = ["You cannot send an empty reply."]
        with xfail_untranslated_messages(config, locale, msgids):
            assert gettext(msgids[0]) not in resp.data.decode("utf-8")
        seen_reply = SeenReply.query.filter_by(journalist_id=journo.id).one_or_none()
        assert seen_reply


def test_unauthorized_access_redirects_to_login(journalist_app):
    with journalist_app.test_client() as app:
        with InstrumentedApp(journalist_app) as ins:
            resp = app.get(url_for("main.index"))
            ins.assert_redirects(resp, url_for("main.login"))


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_login_throttle(config, journalist_app, test_journo, locale):
    with journalist_app.test_client() as app:
        with InstrumentedApp(app) as ins:
            for _ in range(Journalist._MAX_LOGIN_ATTEMPTS_PER_PERIOD):
                resp = app.post(
                    url_for("main.login"),
                    data=dict(
                        username=test_journo["username"],
                        password="invalid",
                        token="invalid",
                    ),
                )
                assert resp.status_code == 200
                text = resp.data.decode("utf-8")
                assert "Login failed" in text

            resp = app.post(
                url_for("main.login", l=locale),
                data=dict(
                    username=test_journo["username"],
                    password="invalid",
                    token="invalid",
                ),
            )
            assert page_language(resp.data) == language_tag(locale)
            msgids = [
                "Login failed.",
                "Please wait at least {num} second before logging in again.",
            ]
            with xfail_untranslated_messages(config, locale, msgids):
                ins.assert_message_flashed(
                    "{} {}".format(
                        gettext(msgids[0]),
                        ngettext(
                            msgids[1],
                            "Please wait at least {num} seconds before logging in again.",
                            Journalist._LOGIN_ATTEMPT_PERIOD,
                        ).format(num=Journalist._LOGIN_ATTEMPT_PERIOD),
                    ),
                    "error",
                )


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_login_throttle_is_not_global(config, journalist_app, test_journo, test_admin, locale):
    """The login throttling should be per-user, not global. Global login
    throttling can prevent all users logging into the application."""
    with journalist_app.test_client() as app:
        with InstrumentedApp(app) as ins:
            for _ in range(Journalist._MAX_LOGIN_ATTEMPTS_PER_PERIOD):
                resp = app.post(
                    url_for("main.login", l=locale),
                    data=dict(
                        username=test_journo["username"],
                        password="invalid",
                        token="invalid",
                    ),
                )
                assert page_language(resp.data) == language_tag(locale)
                msgids = ["Login failed."]
                with xfail_untranslated_messages(config, locale, msgids):
                    assert gettext(msgids[0]) in resp.data.decode("utf-8")

            resp = app.post(
                url_for("main.login", l=locale),
                data=dict(
                    username=test_journo["username"],
                    password="invalid",
                    token="invalid",
                ),
            )
            assert page_language(resp.data) == language_tag(locale)
            msgids = [
                "Login failed.",
                "Please wait at least {num} second before logging in again.",
            ]
            with xfail_untranslated_messages(config, locale, msgids):
                ins.assert_message_flashed(
                    "{} {}".format(
                        gettext(msgids[0]),
                        ngettext(
                            msgids[1],
                            "Please wait at least {num} seconds before logging in again.",
                            Journalist._LOGIN_ATTEMPT_PERIOD,
                        ).format(num=Journalist._LOGIN_ATTEMPT_PERIOD),
                    ),
                    "error",
                )

        # A different user should be able to login
        resp = app.post(
            url_for("main.login", l=locale),
            data=dict(
                username=test_admin["username"],
                password=test_admin["password"],
                token=TOTP(test_admin["otp_secret"]).now(),
            ),
            follow_redirects=True,
        )
        assert page_language(resp.data) == language_tag(locale)
        msgids = ["All Sources"]
        with xfail_untranslated_messages(config, locale, msgids):
            assert gettext(msgids[0]) in resp.data.decode("utf-8")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_login_invalid_credentials(config, journalist_app, test_journo, locale):
    with journalist_app.test_client() as app:
        resp = app.post(
            url_for("main.login", l=locale),
            data=dict(username=test_journo["username"], password="invalid", token="mocked"),
        )
        assert page_language(resp.data) == language_tag(locale)
        msgids = ["Login failed."]
        with xfail_untranslated_messages(config, locale, msgids):
            assert gettext(msgids[0]) in resp.data.decode("utf-8")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_validate_redirect(config, journalist_app, locale):
    with journalist_app.test_client() as app:
        resp = app.post(url_for("main.index", l=locale), follow_redirects=True)
        assert page_language(resp.data) == language_tag(locale)
        msgids = ["Login to access the journalist interface"]
        with xfail_untranslated_messages(config, locale, msgids):
            assert gettext(msgids[0]) in resp.data.decode("utf-8")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_login_valid_credentials(config, journalist_app, test_journo, locale):
    with journalist_app.test_client() as app:
        resp = app.post(
            url_for("main.login", l=locale),
            data=dict(
                username=test_journo["username"],
                password=test_journo["password"],
                token=TOTP(test_journo["otp_secret"]).now(),
            ),
            follow_redirects=True,
        )
        assert page_language(resp.data) == language_tag(locale)
        msgids = ["All Sources", "There are no submissions!"]
        with xfail_untranslated_messages(config, locale, msgids):
            resp_text = resp.data.decode("utf-8")
            for msgid in msgids:
                assert gettext(msgid) in resp_text


def test_admin_login_redirects_to_index(journalist_app, test_admin):
    with journalist_app.test_client() as app:
        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for("main.login"),
                data=dict(
                    username=test_admin["username"],
                    password=test_admin["password"],
                    token=TOTP(test_admin["otp_secret"]).now(),
                ),
                follow_redirects=False,
            )
            ins.assert_redirects(resp, url_for("main.index"))


def test_user_login_redirects_to_index(journalist_app, test_journo):
    with journalist_app.test_client() as app:
        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for("main.login"),
                data=dict(
                    username=test_journo["username"],
                    password=test_journo["password"],
                    token=TOTP(test_journo["otp_secret"]).now(),
                ),
                follow_redirects=False,
            )
            ins.assert_redirects(resp, url_for("main.index"))


def test_admin_has_link_to_edit_account_page_in_index_page(journalist_app, test_admin):
    with journalist_app.test_client() as app:
        resp = app.post(
            url_for("main.login"),
            data=dict(
                username=test_admin["username"],
                password=test_admin["password"],
                token=TOTP(test_admin["otp_secret"]).now(),
            ),
            follow_redirects=True,
        )
    edit_account_link = '<a href="/account/account" ' 'id="link-edit-account">'
    text = resp.data.decode("utf-8")
    assert edit_account_link in text


def test_user_has_link_to_edit_account_page_in_index_page(journalist_app, test_journo):
    with journalist_app.test_client() as app:
        resp = app.post(
            url_for("main.login"),
            data=dict(
                username=test_journo["username"],
                password=test_journo["password"],
                token=TOTP(test_journo["otp_secret"]).now(),
            ),
            follow_redirects=True,
        )
    edit_account_link = '<a href="/account/account" ' 'id="link-edit-account">'
    text = resp.data.decode("utf-8")
    assert edit_account_link in text


def test_admin_has_link_to_admin_index_page_in_index_page(journalist_app, test_admin):
    with journalist_app.test_client() as app:
        resp = app.post(
            url_for("main.login"),
            data=dict(
                username=test_admin["username"],
                password=test_admin["password"],
                token=TOTP(test_admin["otp_secret"]).now(),
            ),
            follow_redirects=True,
        )
    text = resp.data.decode("utf-8")
    assert '<a href="/admin/" id="link-admin-index">' in text


def test_user_lacks_link_to_admin_index_page_in_index_page(journalist_app, test_journo):
    with journalist_app.test_client() as app:
        resp = app.post(
            url_for("main.login"),
            data=dict(
                username=test_journo["username"],
                password=test_journo["password"],
                token=TOTP(test_journo["otp_secret"]).now(),
            ),
            follow_redirects=True,
        )
    text = resp.data.decode("utf-8")
    assert '<a href="/admin/" id="link-admin-index">' not in text


def test_admin_logout_redirects_to_index(config, journalist_app, test_admin):
    with journalist_app.test_client() as app:
        with InstrumentedApp(journalist_app) as ins:
            login_journalist(
                app,
                test_admin["username"],
                test_admin["password"],
                test_admin["otp_secret"],
            )
            resp = app.get(url_for("main.logout"))
            ins.assert_redirects(resp, url_for("main.index"))


def test_user_logout_redirects_to_index(config, journalist_app, test_journo):
    with journalist_app.test_client() as app:
        with InstrumentedApp(journalist_app) as ins:
            login_journalist(
                app,
                test_journo["username"],
                test_journo["password"],
                test_journo["otp_secret"],
            )
            resp = app.get(url_for("main.logout"))
            ins.assert_redirects(resp, url_for("main.index"))


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_admin_index(config, journalist_app, test_admin, locale):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )
        resp = app.get(url_for("admin.index", l=locale))
        assert page_language(resp.data) == language_tag(locale)
        msgids = ["Admin Interface"]
        with xfail_untranslated_messages(config, locale, msgids):
            assert gettext(msgids[0]) in resp.data.decode("utf-8")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_admin_delete_user(config, journalist_app, test_admin, test_journo, locale):
    # Verify journalist is in the database
    with journalist_app.app_context():
        assert Journalist.query.get(test_journo["id"]) is not None

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )
        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for("admin.delete_user", user_id=test_journo["id"], l=locale),
                follow_redirects=True,
            )

            assert page_language(resp.data) == language_tag(locale)
            msgids = ["Deleted user '{user}'."]
            with xfail_untranslated_messages(config, locale, msgids):
                ins.assert_message_flashed(
                    gettext(msgids[0]).format(user=test_journo["username"]),
                    "notification",
                )

    # Verify journalist is no longer in the database
    with journalist_app.app_context():
        assert Journalist.query.get(test_journo["id"]) is None


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_admin_cannot_delete_self(config, journalist_app, test_admin, test_journo, locale):
    # Verify journalist is in the database
    with journalist_app.app_context():
        assert Journalist.query.get(test_journo["id"]) is not None

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )
        resp = app.post(
            url_for("admin.delete_user", user_id=test_admin["id"], l=locale),
            follow_redirects=True,
        )

        # Assert correct interface behavior
        assert resp.status_code == 403

        resp = app.get(url_for("admin.index", l=locale), follow_redirects=True)
        assert resp.status_code == 200
        assert page_language(resp.data) == language_tag(locale)
        msgids = ["Admin Interface", "Edit user {username}", "Delete user {username}"]
        with xfail_untranslated_messages(config, locale, msgids):
            resp_text = resp.data.decode("utf-8")
            assert gettext(msgids[0]) in resp_text

            # The user can be edited and deleted
            assert (
                escape(gettext("Edit user {username}").format(username=test_journo["username"]))
                in resp_text
            )
            assert (
                escape(gettext("Delete user {username}").format(username=test_journo["username"]))
                in resp_text
            )
            # The admin can be edited but cannot deleted
            assert (
                escape(gettext("Edit user {username}").format(username=test_admin["username"]))
                in resp_text
            )
            assert (
                escape(gettext("Delete user {username}").format(username=test_admin["username"]))
                not in resp_text
            )


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_admin_cannot_edit_own_password_without_validation(
    config, journalist_app, test_admin, locale, mocker
):
    mocked_error_logger = mocker.patch("journalist.app.logger.error")

    with journalist_app.test_client() as app:
        login_journalist(
            app, test_admin["username"], test_admin["password"], test_admin["otp_secret"]
        )

        resp = app.post(
            url_for("admin.new_password", user_id=test_admin["id"], l=locale),
            data=dict(password=VALID_PASSWORD),
            follow_redirects=True,
        )
        assert resp.status_code == 403

    mocked_error_logger.assert_called_once_with(
        "Admin {} tried to change their password without validation.".format(test_admin["username"])
    )


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_admin_edits_user_password_success_response(
    config, journalist_app, test_admin, test_journo, locale
):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        resp = app.post(
            url_for("admin.new_password", user_id=test_journo["id"], l=locale),
            data=dict(password=VALID_PASSWORD_2),
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert page_language(resp.data) == language_tag(locale)
        msgids = [
            "Password updated. Don't forget to save it in your KeePassX database. New password:"
        ]
        with xfail_untranslated_messages(config, locale, msgids):
            resp_text = resp.data.decode("utf-8")
            assert escape(gettext(msgids[0])) in resp_text
            assert VALID_PASSWORD_2 in resp_text


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_admin_edits_user_password_session_invalidate(
    config, journalist_app, test_admin, test_journo, locale
):
    # Start the journalist session.
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )

        # Change the journalist password via an admin session.
        with journalist_app.test_client() as admin_app:
            login_journalist(
                admin_app,
                test_admin["username"],
                test_admin["password"],
                test_admin["otp_secret"],
            )

            resp = admin_app.post(
                url_for("admin.new_password", user_id=test_journo["id"], l=locale),
                data=dict(password=VALID_PASSWORD_2),
                follow_redirects=True,
            )
            assert resp.status_code == 200
            assert page_language(resp.data) == language_tag(locale)
            msgids = [
                "Password updated. Don't forget to save it in your KeePassX database. New password:"
            ]
            with xfail_untranslated_messages(config, locale, msgids):
                resp_text = resp.data.decode("utf-8")
                assert escape(gettext(msgids[0])) in resp_text
                assert VALID_PASSWORD_2 in resp_text


def test_admin_deletes_invalid_user_404(journalist_app, test_admin):
    with journalist_app.app_context():
        invalid_id = db.session.query(func.max(Journalist.id)).scalar() + 1

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )
        resp = app.post(url_for("admin.delete_user", user_id=invalid_id))
        assert resp.status_code == 404


def test_admin_deletes_deleted_user_403(journalist_app, test_admin):
    with journalist_app.app_context():
        deleted = Journalist.get_deleted()
        db.session.commit()
        deleted_id = deleted.id

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )
        resp = app.post(url_for("admin.delete_user", user_id=deleted_id))
        assert resp.status_code == 403


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_admin_edits_user_password_error_response(
    config, journalist_app, test_admin, test_journo, locale
):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        with patch("sqlalchemy.orm.scoping.scoped_session.commit", side_effect=Exception()):
            with InstrumentedApp(journalist_app) as ins:
                resp = app.post(
                    url_for("admin.new_password", user_id=test_journo["id"], l=locale),
                    data=dict(password=VALID_PASSWORD_2),
                    follow_redirects=True,
                )
                assert page_language(resp.data) == language_tag(locale)
                msgids = [
                    "There was an error, and the new password might not have been "
                    "saved correctly. To prevent you from getting locked "
                    "out of your account, you should reset your password again."
                ]
                with xfail_untranslated_messages(config, locale, msgids):
                    ins.assert_message_flashed(gettext(msgids[0]), "error")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_user_edits_password_success_response(config, journalist_app, test_journo, locale):
    with journalist_app.test_client() as app:
        login_journalist(
            app, test_journo["username"], test_journo["password"], test_journo["otp_secret"]
        )
        token = TOTP(test_journo["otp_secret"]).now()
        resp = app.post(
            url_for("account.new_password", l=locale),
            data=dict(
                current_password=test_journo["password"],
                token=token,
                password=VALID_PASSWORD_2,
            ),
            follow_redirects=True,
        )

        msgids = [
            "Password updated. Don't forget to save it in your KeePassX database. New password:"
        ]
        with xfail_untranslated_messages(config, locale, msgids):
            resp_text = resp.data.decode("utf-8")
            assert escape(gettext(msgids[0])) in resp_text
            assert VALID_PASSWORD_2 in resp_text


def test_user_edits_password_expires_session(journalist_app, test_journo):
    with journalist_app.test_client() as app:
        login_journalist(
            app, test_journo["username"], test_journo["password"], test_journo["otp_secret"]
        )
        assert "uid" in session

        with InstrumentedApp(journalist_app) as ins:
            token = TOTP(test_journo["otp_secret"]).now()
            resp = app.post(
                url_for("account.new_password"),
                data=dict(
                    current_password=test_journo["password"],
                    token=token,
                    password=VALID_PASSWORD_2,
                ),
            )

            ins.assert_redirects(resp, url_for("main.login"))

        # verify the session was expired after the password was changed
        assert session.uid is None and session.user is None


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_user_edits_password_error_response(config, journalist_app, test_journo, locale):
    with journalist_app.test_client() as app:
        login_journalist(
            app, test_journo["username"], test_journo["password"], test_journo["otp_secret"]
        )

        # patch token verification because there are multiple commits
        # to the database and this isolates the one we want to fail
        with patch.object(Journalist, "verify_2fa_token", return_value="token"):
            with patch.object(db.session, "commit", side_effect=[None, None, Exception()]):
                with InstrumentedApp(journalist_app) as ins:
                    resp = app.post(
                        url_for("account.new_password", l=locale),
                        data=dict(
                            current_password=test_journo["password"],
                            token="mocked",
                            password=VALID_PASSWORD_2,
                        ),
                        follow_redirects=True,
                    )

                    assert page_language(resp.data) == language_tag(locale)
                    msgids = [
                        (
                            "There was an error, and the new password might not have been "
                            "saved correctly. To prevent you from getting locked "
                            "out of your account, you should reset your password again."
                        )
                    ]
                    with xfail_untranslated_messages(config, locale, msgids):
                        ins.assert_message_flashed(gettext(msgids[0]), "error")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_admin_add_user_when_username_already_taken(config, journalist_app, test_admin, locale):
    with journalist_app.test_client() as client:
        login_journalist(
            client,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )
        with InstrumentedApp(journalist_app) as ins:
            resp = client.post(
                url_for("admin.add_user", l=locale),
                data=dict(
                    username=test_admin["username"],
                    first_name="",
                    last_name="",
                    password=VALID_PASSWORD,
                    otp_secret="",
                    is_admin=None,
                ),
            )
            assert page_language(resp.data) == language_tag(locale)

            msgids = ['Username "{username}" already taken.']
            with xfail_untranslated_messages(config, locale, msgids):
                ins.assert_message_flashed(
                    gettext(msgids[0]).format(username=test_admin["username"]), "error"
                )


def test_max_password_length():
    """Creating a Journalist with a password that is greater than the
    maximum password length should raise an exception"""
    overly_long_password = VALID_PASSWORD + "a" * (
        Journalist.MAX_PASSWORD_LEN - len(VALID_PASSWORD) + 1
    )
    with pytest.raises(InvalidPasswordLength):
        Journalist(username="My Password is Too Big!", password=overly_long_password)


def test_login_password_too_long(journalist_app, test_journo, mocker):
    mocked_error_logger = mocker.patch("journalist.app.logger.error")
    with journalist_app.test_client() as app:
        resp = app.post(
            url_for("main.login"),
            data=dict(
                username=test_journo["username"],
                password="a" * (Journalist.MAX_PASSWORD_LEN + 1),
                token=TOTP(test_journo["otp_secret"]).now(),
            ),
        )
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "Login failed" in text
    mocked_error_logger.assert_called_once_with(
        "Login for '{}' failed: Password is too long.".format(test_journo["username"])
    )


def test_min_password_length():
    """Creating a Journalist with a password that is smaller than the
    minimum password length should raise an exception. This uses the
    magic number 7 below to get around the "diceware-like" requirement
    that may cause a failure before the length check.
    """
    password = ("a " * 7)[0 : (Journalist.MIN_PASSWORD_LEN - 1)]
    with pytest.raises(InvalidPasswordLength):
        Journalist(username="My Password is Too Small!", password=password)


def test_admin_edits_user_password_too_long_warning(journalist_app, test_admin, test_journo):
    # append a bunch of a's to a diceware password to keep it "diceware-like"
    overly_long_password = VALID_PASSWORD + "a" * (
        Journalist.MAX_PASSWORD_LEN - len(VALID_PASSWORD) + 1
    )

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )
        with InstrumentedApp(journalist_app) as ins:
            app.post(
                url_for("admin.new_password", user_id=test_journo["id"]),
                data=dict(
                    username=test_journo["username"],
                    first_name="",
                    last_name="",
                    is_admin=None,
                    password=overly_long_password,
                ),
                follow_redirects=True,
            )

            ins.assert_message_flashed(
                "The password you submitted is invalid. " "Password not changed.",
                "error",
            )


def test_user_edits_password_too_long_warning(config, journalist_app, test_journo):
    overly_long_password = VALID_PASSWORD + "a" * (
        Journalist.MAX_PASSWORD_LEN - len(VALID_PASSWORD) + 1
    )

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )

        with InstrumentedApp(journalist_app) as ins:
            app.post(
                url_for("account.new_password"),
                data=dict(
                    username=test_journo["username"],
                    first_name="",
                    last_name="",
                    is_admin=None,
                    token=TOTP(test_journo["otp_secret"]).now(),
                    current_password=test_journo["password"],
                    password=overly_long_password,
                ),
                follow_redirects=True,
            )

            ins.assert_message_flashed(
                "The password you submitted is invalid. " "Password not changed.",
                "error",
            )


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_admin_add_user_password_too_long_warning(config, journalist_app, test_admin, locale):
    overly_long_password = VALID_PASSWORD + "a" * (
        Journalist.MAX_PASSWORD_LEN - len(VALID_PASSWORD) + 1
    )
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for("admin.add_user", l=locale),
                data=dict(
                    username="dellsberg",
                    first_name="",
                    last_name="",
                    password=overly_long_password,
                    otp_secret="",
                    is_admin=None,
                ),
            )

            assert page_language(resp.data) == language_tag(locale)
            msgids = [
                "There was an error with the autogenerated password. User not "
                "created. Please try again."
            ]
            with xfail_untranslated_messages(config, locale, msgids):
                ins.assert_message_flashed(gettext(msgids[0]), "error")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_admin_add_user_first_name_too_long_warning(config, journalist_app, test_admin, locale):
    with journalist_app.test_client() as app:
        overly_long_name = "a" * (Journalist.MAX_NAME_LEN + 1)
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        resp = app.post(
            url_for("admin.add_user", l=locale),
            data=dict(
                username=test_admin["username"],
                first_name=overly_long_name,
                last_name="",
                password=VALID_PASSWORD,
                otp_secret="",
                is_admin=None,
            ),
        )
        assert page_language(resp.data) == language_tag(locale)
        msgids = ["Cannot be longer than {num} character."]
        with xfail_untranslated_messages(config, locale, msgids):
            assert ngettext(
                "Cannot be longer than {num} character.",
                "Cannot be longer than {num} characters.",
                Journalist.MAX_NAME_LEN,
            ).format(num=Journalist.MAX_NAME_LEN) in resp.data.decode("utf-8")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_admin_add_user_last_name_too_long_warning(config, journalist_app, test_admin, locale):
    with journalist_app.test_client() as app:
        overly_long_name = "a" * (Journalist.MAX_NAME_LEN + 1)
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        resp = app.post(
            url_for("admin.add_user", l=locale),
            data=dict(
                username=test_admin["username"],
                first_name="",
                last_name=overly_long_name,
                password=VALID_PASSWORD,
                otp_secret="",
                is_admin=None,
            ),
        )
        assert page_language(resp.data) == language_tag(locale)
        msgids = ["Cannot be longer than {num} character."]
        with xfail_untranslated_messages(config, locale, msgids):
            assert ngettext(
                "Cannot be longer than {num} character.",
                "Cannot be longer than {num} characters.",
                Journalist.MAX_NAME_LEN,
            ).format(num=Journalist.MAX_NAME_LEN) in resp.data.decode("utf-8")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_admin_edits_user_invalid_username_deleted(
    config, journalist_app, test_admin, test_journo, locale
):
    """Test expected error message when admin attempts to change a user's
    username to deleted"""
    new_username = "deleted"
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for("admin.edit_user", user_id=test_admin["id"], l=locale),
                data=dict(username=new_username, first_name="", last_name="", is_admin=None),
                follow_redirects=True,
            )

            assert page_language(resp.data) == language_tag(locale)
            msgids = [
                "Invalid username: {message}",
                "This username is invalid because it is reserved for internal use by the software.",
            ]
            with xfail_untranslated_messages(config, locale, msgids):
                ins.assert_message_flashed(
                    gettext(msgids[0]).format(message=gettext(msgids[1])), "error"
                )


def test_admin_resets_user_hotp_format_non_hexa(journalist_app, test_admin, test_journo):

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        journo = test_journo["journalist"]
        # guard to ensure check below tests the correct condition
        assert journo.is_totp

        old_secret = journo.otp_secret

        non_hexa_secret = "0123456789ABCDZZ0123456789ABCDEF01234567"
        with InstrumentedApp(journalist_app) as ins:
            app.post(
                url_for("admin.reset_two_factor_hotp"),
                data=dict(uid=test_journo["id"], otp_secret=non_hexa_secret),
            )

            # fetch altered DB object
            journo = Journalist.query.get(journo.id)

            new_secret = journo.otp_secret
            assert old_secret == new_secret

            # ensure we didn't accidentally enable hotp
            assert journo.is_totp

            ins.assert_message_flashed(
                "Invalid HOTP secret format: please only submit letters A-F and " "numbers 0-9.",
                "error",
            )


@pytest.mark.parametrize("the_secret", [" ", "    ", "0123456789ABCDEF0123456789ABCDE"])
def test_admin_resets_user_hotp_format_too_short(
    journalist_app, test_admin, test_journo, the_secret
):

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        journo = test_journo["journalist"]
        # guard to ensure check below tests the correct condition
        assert journo.is_totp

        old_secret = journo.otp_secret

        with InstrumentedApp(journalist_app) as ins:
            app.post(
                url_for("admin.reset_two_factor_hotp"),
                data=dict(uid=test_journo["id"], otp_secret=the_secret),
            )

            # fetch altered DB object
            journo = Journalist.query.get(journo.id)

            new_secret = journo.otp_secret
            assert old_secret == new_secret

            # ensure we didn't accidentally enable hotp
            assert journo.is_totp

            ins.assert_message_flashed(
                "HOTP secrets are 40 characters long"
                " - you have entered {num}.".format(num=len(the_secret.replace(" ", ""))),
                "error",
            )


def test_admin_resets_user_hotp(journalist_app, test_admin, test_journo):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        journo = test_journo["journalist"]
        old_secret = journo.otp_secret

        valid_secret = "DEADBEEF01234567DEADBEEF01234567DEADBEEF"
        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for("admin.reset_two_factor_hotp"),
                data=dict(uid=test_journo["id"], otp_secret=valid_secret),
            )

            # fetch altered DB object
            journo = Journalist.query.get(journo.id)

            new_secret = journo.otp_secret
            assert old_secret != new_secret
            assert not journo.is_totp

            # Redirect to admin 2FA view
            ins.assert_redirects(resp, url_for("admin.new_user_two_factor", uid=journo.id))


def test_admin_resets_user_hotp_error(mocker, journalist_app, test_admin, test_journo):

    bad_secret = "0123456789ABCDZZ0123456789ABCDZZ01234567"
    error_message = "SOMETHING WRONG!"
    mocked_error_logger = mocker.patch("journalist.app.logger.error")
    old_secret = test_journo["otp_secret"]

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        mocker.patch(
            "models.Journalist.set_hotp_secret",
            side_effect=binascii.Error(error_message),
        )

        with InstrumentedApp(journalist_app) as ins:
            app.post(
                url_for("admin.reset_two_factor_hotp"),
                data=dict(uid=test_journo["id"], otp_secret=bad_secret),
            )
            ins.assert_message_flashed(
                "An unexpected error occurred! " "Please inform your admin.", "error"
            )

    # Re-fetch journalist to get fresh DB instance
    user = Journalist.query.get(test_journo["id"])
    new_secret = user.otp_secret

    assert new_secret == old_secret

    mocked_error_logger.assert_called_once_with(
        "set_hotp_secret '{}' (id {}) failed: {}".format(
            bad_secret, test_journo["id"], error_message
        )
    )


def test_user_resets_hotp(journalist_app, test_journo):
    old_secret = test_journo["otp_secret"]
    new_secret = "0123456789ABCDEF0123456789ABCDEF01234567"

    # Precondition
    assert new_secret != old_secret

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )

        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for("account.reset_two_factor_hotp"),
                data=dict(otp_secret=new_secret),
            )
            # should redirect to verification page
            ins.assert_redirects(resp, url_for("account.new_two_factor"))

    # Re-fetch journalist to get fresh DB instance
    user = Journalist.query.get(test_journo["id"])
    new_secret = user.otp_secret

    assert old_secret != new_secret


def test_user_resets_user_hotp_format_non_hexa(journalist_app, test_journo):
    old_secret = test_journo["otp_secret"]

    non_hexa_secret = "0123456789ABCDZZ0123456789ABCDEF01234567"
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )

        with InstrumentedApp(journalist_app) as ins:
            app.post(
                url_for("account.reset_two_factor_hotp"),
                data=dict(otp_secret=non_hexa_secret),
            )
            ins.assert_message_flashed(
                "Invalid HOTP secret format: " "please only submit letters A-F and numbers 0-9.",
                "error",
            )

    # Re-fetch journalist to get fresh DB instance
    user = Journalist.query.get(test_journo["id"])
    new_secret = user.otp_secret

    assert old_secret == new_secret


def test_user_resets_user_hotp_error(mocker, journalist_app, test_journo):
    bad_secret = "0123456789ABCDZZ0123456789ABCDZZ01234567"
    old_secret = test_journo["otp_secret"]
    error_message = "SOMETHING WRONG!"
    mocked_error_logger = mocker.patch("journalist.app.logger.error")

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )

        mocker.patch(
            "models.Journalist.set_hotp_secret",
            side_effect=binascii.Error(error_message),
        )

        with InstrumentedApp(journalist_app) as ins:
            app.post(
                url_for("account.reset_two_factor_hotp"),
                data=dict(otp_secret=bad_secret),
            )
            ins.assert_message_flashed(
                "An unexpected error occurred! Please inform your " "admin.", "error"
            )

    # Re-fetch journalist to get fresh DB instance
    user = Journalist.query.get(test_journo["id"])
    new_secret = user.otp_secret

    assert old_secret == new_secret
    mocked_error_logger.assert_called_once_with(
        "set_hotp_secret '{}' (id {}) failed: {}".format(
            bad_secret, test_journo["id"], error_message
        )
    )


def test_admin_resets_user_totp(journalist_app, test_admin, test_journo):
    old_secret = test_journo["otp_secret"]

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for("admin.reset_two_factor_totp"), data=dict(uid=test_journo["id"])
            )
            ins.assert_redirects(resp, url_for("admin.new_user_two_factor", uid=test_journo["id"]))

    # Re-fetch journalist to get fresh DB instance
    user = Journalist.query.get(test_journo["id"])
    new_secret = user.otp_secret

    assert new_secret != old_secret


def test_user_resets_totp(journalist_app, test_journo):
    old_secret = test_journo["otp_secret"]

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )

        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(url_for("account.reset_two_factor_totp"))
            # should redirect to verification page
            ins.assert_redirects(resp, url_for("account.new_two_factor"))

    # Re-fetch journalist to get fresh DB instance
    user = Journalist.query.get(test_journo["id"])
    new_secret = user.otp_secret

    assert new_secret != old_secret


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_admin_resets_hotp_with_missing_otp_secret_key(config, journalist_app, test_admin, locale):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )
        resp = app.post(
            url_for("admin.reset_two_factor_hotp", l=locale),
            data=dict(uid=test_admin["id"]),
        )

        assert page_language(resp.data) == language_tag(locale)
        msgids = ["Change HOTP Secret"]
        with xfail_untranslated_messages(config, locale, msgids):
            assert gettext(msgids[0]) in resp.data.decode("utf-8")


def test_admin_new_user_2fa_redirect(journalist_app, test_admin, test_journo):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )
        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for("admin.new_user_two_factor", uid=test_journo["id"]),
                data=dict(token=TOTP(test_journo["otp_secret"]).now()),
            )
            ins.assert_redirects(resp, url_for("admin.index"))


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_http_get_on_admin_new_user_two_factor_page(
    config, journalist_app, test_admin, test_journo, locale
):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )
        resp = app.get(
            url_for("admin.new_user_two_factor", uid=test_journo["id"], l=locale),
        )

        assert page_language(resp.data) == language_tag(locale)
        msgids = ["Enable FreeOTP"]
        with xfail_untranslated_messages(config, locale, msgids):
            assert gettext(msgids[0]) in resp.data.decode("utf-8")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_http_get_on_admin_add_user_page(config, journalist_app, test_admin, locale):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )
        resp = app.get(url_for("admin.add_user", l=locale))
        assert page_language(resp.data) == language_tag(locale)
        msgids = ["ADD USER"]
        with xfail_untranslated_messages(config, locale, msgids):
            assert gettext(msgids[0]) in resp.data.decode("utf-8")


def test_admin_add_user(journalist_app, test_admin):
    username = "dellsberg"

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for("admin.add_user"),
                data=dict(
                    username=username,
                    first_name="",
                    last_name="",
                    password=VALID_PASSWORD,
                    otp_secret="",
                    is_admin=None,
                ),
            )

            new_user = Journalist.query.filter_by(username=username).one()
            ins.assert_redirects(resp, url_for("admin.new_user_two_factor", uid=new_user.id))


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_admin_add_user_with_invalid_username(config, journalist_app, test_admin, locale):
    username = "deleted"

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        resp = app.post(
            url_for("admin.add_user", l=locale),
            data=dict(
                username=username,
                first_name="",
                last_name="",
                password=VALID_PASSWORD,
                otp_secret="",
                is_admin=None,
            ),
        )
        assert page_language(resp.data) == language_tag(locale)
        msgids = [
            "This username is invalid because it is reserved for internal use by the software."
        ]
        with xfail_untranslated_messages(config, locale, msgids):
            assert gettext(msgids[0]) in resp.data.decode("utf-8")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_deleted_user_cannot_login(config, journalist_app, locale):
    with journalist_app.app_context():
        user = Journalist.get_deleted()
        password = PassphraseGenerator.get_default().generate_passphrase()
        user.set_password(password)
        db.session.commit()
        otp_secret = user.otp_secret

    with InstrumentedApp(journalist_app) as ins:
        # Verify that deleted user is not able to login
        with journalist_app.test_client() as app:
            resp = app.post(
                url_for("main.login", l=locale),
                data=dict(username="deleted", password=password, token=TOTP(otp_secret).now()),
            )
            assert page_language(resp.data) == language_tag(locale)
            msgids = [
                "Login failed.",
                (
                    "Please wait for a new code from your two-factor mobile"
                    " app or security key before trying again."
                ),
            ]
            with xfail_untranslated_messages(config, locale, msgids):
                ins.assert_message_flashed(
                    "{} {}".format(
                        gettext(msgids[0]),
                        gettext(msgids[1]),
                    ),
                    "error",
                )


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_deleted_user_cannot_login_exception(journalist_app, locale):
    with journalist_app.app_context():
        user = Journalist.get_deleted()
        password = PassphraseGenerator.get_default().generate_passphrase()
        user.set_password(password)
        db.session.commit()
        otp_secret = user.otp_secret

    with journalist_app.test_request_context("/"):
        with pytest.raises(InvalidUsernameException):
            Journalist.login("deleted", password, TOTP(otp_secret).now())


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_admin_add_user_without_username(config, journalist_app, test_admin, locale):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        resp = app.post(
            url_for("admin.add_user", l=locale),
            data=dict(
                username="",
                first_name="",
                last_name="",
                password=VALID_PASSWORD,
                otp_secret="",
                is_admin=None,
            ),
        )

        assert page_language(resp.data) == language_tag(locale)
        msgids = ["This field is required."]
        with xfail_untranslated_messages(config, locale, msgids):
            assert gettext(msgids[0]) in resp.data.decode("utf-8")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_admin_add_user_too_short_username(config, journalist_app, test_admin, locale):
    username = "a" * (Journalist.MIN_USERNAME_LEN - 1)

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        resp = app.post(
            url_for("admin.add_user", l=locale),
            data=dict(
                username=username,
                first_name="",
                last_name="",
                password="pentagonpapers",
                password_again="pentagonpapers",
                otp_secret="",
                is_admin=None,
            ),
        )
        assert page_language(resp.data) == language_tag(locale)
        msgids = ["Must be at least {num} character long."]
        with xfail_untranslated_messages(config, locale, msgids):
            assert ngettext(
                "Must be at least {num} character long.",
                "Must be at least {num} characters long.",
                Journalist.MIN_USERNAME_LEN,
            ).format(num=Journalist.MIN_USERNAME_LEN) in resp.data.decode("utf-8")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize(
    "locale, secret",
    (
        (locale, "a" * i)
        for locale in get_test_locales()
        for i in get_plural_tests()[locale]  # pylint: disable=undefined-variable
        if i != 0
    ),
)
def test_admin_add_user_yubikey_odd_length(config, journalist_app, test_admin, locale, secret):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        resp = app.post(
            url_for("admin.add_user", l=locale),
            data=dict(
                username="dellsberg",
                first_name="",
                last_name="",
                password=VALID_PASSWORD,
                password_again=VALID_PASSWORD,
                is_admin=None,
                is_hotp=True,
                otp_secret=secret,
            ),
        )
        journalist_app.logger.critical("response: %s", resp.data)
        assert page_language(resp.data) == language_tag(locale)
        msgids = ["HOTP secrets are 40 characters long - you have entered {num}."]
        with xfail_untranslated_messages(config, locale, msgids):
            assert ngettext(
                "HOTP secrets are 40 characters long - you have entered {num}.",
                "HOTP secrets are 40 characters long - you have entered {num}.",
                len(secret),
            ).format(num=len(secret)) in resp.data.decode("utf-8")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize(
    "locale, secret",
    ((locale, " " * i) for locale in get_test_locales() for i in range(3)),
)
def test_admin_add_user_yubikey_blank_secret(config, journalist_app, test_admin, locale, secret):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        resp = app.post(
            url_for("admin.add_user", l=locale),
            data=dict(
                username="dellsberg",
                first_name="",
                last_name="",
                password=VALID_PASSWORD,
                password_again=VALID_PASSWORD,
                is_admin=None,
                is_hotp=True,
                otp_secret=secret,
            ),
        )

        assert page_language(resp.data) == language_tag(locale)
        msgids = ['The "otp_secret" field is required when "is_hotp" is set.']
        with xfail_untranslated_messages(config, locale, msgids):
            # Should redirect to the token verification page
            assert gettext(msgids[0]) in resp.data.decode("utf-8")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_admin_add_user_yubikey_valid_length(config, journalist_app, test_admin, locale):
    otp = "1234567890123456789012345678901234567890"

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        resp = app.post(
            url_for("admin.add_user", l=locale),
            data=dict(
                username="dellsberg",
                first_name="",
                last_name="",
                password=VALID_PASSWORD,
                password_again=VALID_PASSWORD,
                is_admin=None,
                is_hotp=True,
                otp_secret=otp,
            ),
            follow_redirects=True,
        )
        assert page_language(resp.data) == language_tag(locale)
        msgids = ["Enable YubiKey (OATH-HOTP)"]
        with xfail_untranslated_messages(config, locale, msgids):
            # Should redirect to the token verification page
            assert gettext(msgids[0]) in resp.data.decode("utf-8")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_admin_add_user_yubikey_correct_length_with_whitespace(
    config, journalist_app, test_admin, locale
):
    otp = "12 34 56 78 90 12 34 56 78 90 12 34 56 78 90 12 34 56 78 90"

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        resp = app.post(
            url_for("admin.add_user", l=locale),
            data=dict(
                username="dellsberg",
                first_name="",
                last_name="",
                password=VALID_PASSWORD,
                password_again=VALID_PASSWORD,
                is_admin=None,
                is_hotp=True,
                otp_secret=otp,
            ),
            follow_redirects=True,
        )
        assert page_language(resp.data) == language_tag(locale)
        msgids = ["Enable YubiKey (OATH-HOTP)"]
        with xfail_untranslated_messages(config, locale, msgids):
            # Should redirect to the token verification page
            assert gettext(msgids[0]) in resp.data.decode("utf-8")


def test_admin_sets_user_to_admin(journalist_app, test_admin):
    new_user = "admin-set-user-to-admin-test"

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        resp = app.post(
            url_for("admin.add_user"),
            data=dict(
                username=new_user,
                first_name="",
                last_name="",
                otp_secret="",
                password=VALID_PASSWORD,
                is_admin=None,
            ),
        )
        assert resp.status_code in (200, 302)

        journo = Journalist.query.filter_by(username=new_user).one()
        # precondition check
        assert journo.is_admin is False

        resp = app.post(
            url_for("admin.edit_user", user_id=journo.id),
            data=dict(first_name="", last_name="", is_admin=True),
        )
        assert resp.status_code in (200, 302)

        journo = Journalist.query.filter_by(username=new_user).one()
        assert journo.is_admin is True


def test_admin_renames_user(journalist_app, test_admin):
    new_user = "admin-renames-user-test"

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        resp = app.post(
            url_for("admin.add_user"),
            data=dict(
                username=new_user,
                first_name="",
                last_name="",
                password=VALID_PASSWORD,
                otp_secret="",
                is_admin=None,
            ),
        )
        assert resp.status_code in (200, 302)
        journo = Journalist.query.filter(Journalist.username == new_user).one()

        new_user = new_user + "a"
        resp = app.post(
            url_for("admin.edit_user", user_id=journo.id),
            data=dict(username=new_user, first_name="", last_name=""),
        )
    assert resp.status_code in (200, 302), resp.data.decode("utf-8")

    # the following will throw an exception if new_user is not found
    # therefore asserting it has been created
    Journalist.query.filter(Journalist.username == new_user).one()


def test_admin_adds_first_name_last_name_to_user(journalist_app, test_admin):
    new_user = "admin-first-name-last-name-user-test"

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        resp = app.post(
            url_for("admin.add_user"),
            data=dict(
                username=new_user,
                first_name="",
                last_name="",
                password=VALID_PASSWORD,
                otp_secret="",
                is_admin=None,
            ),
        )
        assert resp.status_code in (200, 302)
        journo = Journalist.query.filter(Journalist.username == new_user).one()

        resp = app.post(
            url_for("admin.edit_user", user_id=journo.id),
            data=dict(username=new_user, first_name="test name", last_name="test name"),
        )
    assert resp.status_code in (200, 302)

    # the following will throw an exception if new_user is not found
    # therefore asserting it has been created
    Journalist.query.filter(Journalist.username == new_user).one()


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_admin_adds_invalid_first_last_name_to_user(config, journalist_app, test_admin, locale):
    with journalist_app.test_client() as client:
        new_user = "admin-invalid-first-name-last-name-user-test"

        login_journalist(
            client,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        resp = client.post(
            url_for("admin.add_user"),
            data=dict(
                username=new_user,
                first_name="",
                last_name="",
                password=VALID_PASSWORD,
                otp_secret="",
                is_admin=None,
            ),
        )
        assert resp.status_code == 302
        journo = Journalist.query.filter(Journalist.username == new_user).one()

        overly_long_name = "a" * (Journalist.MAX_NAME_LEN + 1)

        with InstrumentedApp(journalist_app) as ins:
            resp = client.post(
                url_for("admin.edit_user", user_id=journo.id, l=locale),
                data=dict(
                    username=new_user,
                    first_name=overly_long_name,
                    last_name="test name",
                ),
                follow_redirects=True,
            )
            assert resp.status_code == 200
            assert page_language(resp.data) == language_tag(locale)

            msgids = ["Name not updated: {message}", "Name too long"]
            with xfail_untranslated_messages(config, locale, msgids):
                ins.assert_message_flashed(
                    gettext(msgids[0]).format(message=gettext("Name too long")), "error"
                )


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_admin_add_user_integrity_error(config, journalist_app, test_admin, mocker, locale):
    mocked_error_logger = mocker.patch("journalist_app.admin.current_app.logger.error")
    mocker.patch(
        "journalist_app.admin.Journalist",
        side_effect=IntegrityError("STATEMENT", "PARAMETERS", None),
    )

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for("admin.add_user", l=locale),
                data=dict(
                    username="username",
                    first_name="",
                    last_name="",
                    password=VALID_PASSWORD,
                    otp_secret="",
                    is_admin=None,
                ),
            )
            assert page_language(resp.data) == language_tag(locale)
            msgids = [
                "An error occurred saving this user to the database. " "Please inform your admin."
            ]
            with xfail_untranslated_messages(config, locale, msgids):
                ins.assert_message_flashed(gettext(msgids[0]), "error")

    log_event = mocked_error_logger.call_args[0][0]
    assert (
        "Adding user 'username' failed: (builtins.NoneType) "
        "None\n[SQL: STATEMENT]\n[parameters: 'PARAMETERS']"
    ) in log_event


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_prevent_document_uploads(config, journalist_app, test_admin, locale):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )
        form = journalist_app_module.forms.SubmissionPreferencesForm(
            prevent_document_uploads=True, min_message_length=0
        )
        app.post(
            url_for("admin.update_submission_preferences"),
            data=form.data,
            follow_redirects=True,
        )
        assert InstanceConfig.get_current().allow_document_uploads is False
        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for("admin.update_submission_preferences", l=locale),
                data=form.data,
                follow_redirects=True,
            )
            assert page_language(resp.data) == language_tag(locale)
            msgids = ["Preferences saved."]
            with xfail_untranslated_messages(config, locale, msgids):
                ins.assert_message_flashed(gettext(msgids[0]), "submission-preferences-success")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_no_prevent_document_uploads(config, journalist_app, test_admin, locale):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )
        form = journalist_app_module.forms.SubmissionPreferencesForm(min_message_length=0)
        app.post(
            url_for("admin.update_submission_preferences"),
            data=form.data,
            follow_redirects=True,
        )
        assert InstanceConfig.get_current().allow_document_uploads is True
        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for("admin.update_submission_preferences", l=locale),
                data=form.data,
                follow_redirects=True,
            )
            assert InstanceConfig.get_current().allow_document_uploads is True
            assert page_language(resp.data) == language_tag(locale)
            msgids = ["Preferences saved."]
            with xfail_untranslated_messages(config, locale, msgids):
                ins.assert_message_flashed(gettext(msgids[0]), "submission-preferences-success")


def test_prevent_document_uploads_invalid(journalist_app, test_admin):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )
        form_true = journalist_app_module.forms.SubmissionPreferencesForm(
            prevent_document_uploads=True, min_message_length=0
        )
        app.post(
            url_for("admin.update_submission_preferences"),
            data=form_true.data,
            follow_redirects=True,
        )
        assert InstanceConfig.get_current().allow_document_uploads is False

        with patch("flask_wtf.FlaskForm.validate_on_submit") as fMock:
            fMock.return_value = False
            form_false = journalist_app_module.forms.SubmissionPreferencesForm(
                prevent_document_uploads=False
            )
            app.post(
                url_for("admin.update_submission_preferences"),
                data=form_false.data,
                follow_redirects=True,
            )
            assert InstanceConfig.get_current().allow_document_uploads is False


def test_message_filtering(journalist_app, test_admin):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )
        # Assert status quo
        assert InstanceConfig.get_current().initial_message_min_len == 0

        # Try to set min length to 10, but don't tick the "prevent short messages" checkbox
        form = journalist_app_module.forms.SubmissionPreferencesForm(
            prevent_short_messages=False, min_message_length=10
        )
        app.post(
            url_for("admin.update_submission_preferences"),
            data=form.data,
            follow_redirects=True,
        )
        # Still 0
        assert InstanceConfig.get_current().initial_message_min_len == 0

        # Inverse, tick the "prevent short messages" checkbox but leave min length at 0
        form = journalist_app_module.forms.SubmissionPreferencesForm(
            prevent_short_messages=True, min_message_length=0
        )
        resp = app.post(
            url_for("admin.update_submission_preferences"),
            data=form.data,
            follow_redirects=True,
        )
        # Still 0
        assert InstanceConfig.get_current().initial_message_min_len == 0
        html = resp.data.decode("utf-8")
        assert "To configure a minimum message length, you must set the required" in html

        # Now tick the "prevent short messages" checkbox
        form = journalist_app_module.forms.SubmissionPreferencesForm(
            prevent_short_messages=True, min_message_length=10
        )
        app.post(
            url_for("admin.update_submission_preferences"),
            data=form.data,
            follow_redirects=True,
        )
        assert InstanceConfig.get_current().initial_message_min_len == 10

        # Submit junk data for min_message_length
        resp = app.post(
            url_for("admin.update_submission_preferences"),
            data={**form.data, "min_message_length": "abcdef"},
            follow_redirects=True,
        )
        html = resp.data.decode("utf-8")
        assert "To configure a minimum message length, you must set the required" in html
        # Now rejecting codenames
        assert InstanceConfig.get_current().reject_message_with_codename is False
        form = journalist_app_module.forms.SubmissionPreferencesForm(reject_codename_messages=True)
        app.post(
            url_for("admin.update_submission_preferences"),
            data=form.data,
            follow_redirects=True,
        )
        assert InstanceConfig.get_current().reject_message_with_codename is True


def test_orgname_default_set(journalist_app, test_admin):
    class dummy_current:
        organization_name = None

    with patch.object(InstanceConfig, "get_current") as iMock:
        with journalist_app.test_client() as app:
            iMock.return_value = dummy_current()
            login_journalist(
                app,
                test_admin["username"],
                test_admin["password"],
                test_admin["otp_secret"],
            )
            assert g.organization_name == "SecureDrop"


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_orgname_valid_succeeds(config, journalist_app, test_admin, locale):
    test_name = "Walden Inquirer"
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )
        form = journalist_app_module.forms.OrgNameForm(organization_name=test_name)
        assert InstanceConfig.get_current().organization_name == "SecureDrop"
        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for("admin.update_org_name", l=locale),
                data=form.data,
                follow_redirects=True,
            )
            assert page_language(resp.data) == language_tag(locale)
            msgids = ["Preferences saved."]
            with xfail_untranslated_messages(config, locale, msgids):
                ins.assert_message_flashed(gettext(msgids[0]), "org-name-success")
            assert InstanceConfig.get_current().organization_name == test_name


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_orgname_null_fails(config, journalist_app, test_admin, locale):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )
        form = journalist_app_module.forms.OrgNameForm(organization_name="")
        assert InstanceConfig.get_current().organization_name == "SecureDrop"
        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for("admin.update_org_name", l=locale),
                data=form.data,
                follow_redirects=True,
            )
            assert page_language(resp.data) == language_tag(locale)
            msgids = ["This field is required."]
            with xfail_untranslated_messages(config, locale, msgids):
                ins.assert_message_flashed(gettext(msgids[0]), "org-name-error")
            assert InstanceConfig.get_current().organization_name == "SecureDrop"


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_orgname_oversized_fails(config, journalist_app, test_admin, locale):
    test_name = "1234567812345678123456781234567812345678123456781234567812345678a"
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )
        form = journalist_app_module.forms.OrgNameForm(organization_name=test_name)
        assert InstanceConfig.get_current().organization_name == "SecureDrop"
        resp = app.post(
            url_for("admin.update_org_name", l=locale),
            data=form.data,
            follow_redirects=True,
        )
        assert page_language(resp.data) == language_tag(locale)
        msgids = ["Cannot be longer than {num} character."]
        with xfail_untranslated_messages(config, locale, msgids):
            assert ngettext(
                "Cannot be longer than {num} character.",
                "Cannot be longer than {num} characters.",
                InstanceConfig.MAX_ORG_NAME_LEN,
            ).format(num=InstanceConfig.MAX_ORG_NAME_LEN) in resp.data.decode("utf-8")
        assert InstanceConfig.get_current().organization_name == "SecureDrop"


def test_logo_default_available(journalist_app, config):
    # if the custom image is available, this test will fail
    custom_image_location = os.path.join(config.SECUREDROP_ROOT, "static/i/custom_logo.png")
    if os.path.exists(custom_image_location):
        os.remove(custom_image_location)

    with journalist_app.test_client() as app:
        logo_url = journalist_app_module.get_logo_url(journalist_app)
        assert logo_url.endswith("/static/i/logo.png")
        response = app.get(logo_url, follow_redirects=False)
        assert response.status_code == 200


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_logo_upload_with_valid_image_succeeds(config, journalist_app, test_admin, locale):
    # Save original logo to restore after test run
    logo_image_location = os.path.join(config.SECUREDROP_ROOT, "static/i/logo.png")
    with open(logo_image_location, "rb") as logo_file:
        original_image = logo_file.read()

    try:
        logo_bytes = base64.decodebytes(
            b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQ"
            b"VR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII="
        )

        with journalist_app.test_client() as app:
            login_journalist(
                app,
                test_admin["username"],
                test_admin["password"],
                test_admin["otp_secret"],
            )
            # Create 1px * 1px 'white' PNG file from its base64 string
            form = journalist_app_module.forms.LogoForm(logo=(BytesIO(logo_bytes), "test.png"))
            # Create 1px * 1px 'white' PNG file from its base64 string
            form = journalist_app_module.forms.LogoForm(logo=(BytesIO(logo_bytes), "test.png"))
            with InstrumentedApp(journalist_app) as ins:
                resp = app.post(
                    url_for("admin.manage_config", l=locale),
                    data=form.data,
                    follow_redirects=True,
                )
                assert page_language(resp.data) == language_tag(locale)
                msgids = ["Image updated."]
                with xfail_untranslated_messages(config, locale, msgids):
                    ins.assert_message_flashed(gettext(msgids[0]), "logo-success")

        with journalist_app.test_client() as app:
            logo_url = journalist_app_module.get_logo_url(journalist_app)
            assert logo_url.endswith("/static/i/custom_logo.png")
            response = app.get(logo_url, follow_redirects=False)
            assert response.status_code == 200
            assert response.data == logo_bytes
    finally:
        # Restore original image to logo location for subsequent tests
        with open(logo_image_location, "wb") as logo_file:
            logo_file.write(original_image)


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_logo_upload_with_invalid_filetype_fails(config, journalist_app, test_admin, locale):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        form = journalist_app_module.forms.LogoForm(logo=(BytesIO(b"filedata"), "bad.exe"))
        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for("admin.manage_config", l=locale),
                data=form.data,
                follow_redirects=True,
            )

            assert page_language(resp.data) == language_tag(locale)
            msgids = ["You can only upload PNG image files."]
            with xfail_untranslated_messages(config, locale, msgids):
                ins.assert_message_flashed(gettext(msgids[0]), "logo-error")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_logo_upload_save_fails(config, journalist_app, test_admin, locale):
    # Save original logo to restore after test run
    logo_image_location = os.path.join(config.SECUREDROP_ROOT, "static/i/logo.png")
    with open(logo_image_location, "rb") as logo_file:
        original_image = logo_file.read()

    try:
        with journalist_app.test_client() as app:
            login_journalist(
                app,
                test_admin["username"],
                test_admin["password"],
                test_admin["otp_secret"],
            )
            # Create 1px * 1px 'white' PNG file from its base64 string
            form = journalist_app_module.forms.LogoForm(
                logo=(
                    BytesIO(
                        base64.decodebytes(
                            b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQ"
                            b"VR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII="
                        )
                    ),
                    "test.png",
                )
            )
            with InstrumentedApp(journalist_app) as ins:
                with patch("werkzeug.datastructures.FileStorage.save") as sMock:
                    sMock.side_effect = Exception
                    resp = app.post(
                        url_for("admin.manage_config", l=locale),
                        data=form.data,
                        follow_redirects=True,
                    )

                    assert page_language(resp.data) == language_tag(locale)
                    msgids = ["Unable to process the image file. Please try another one."]
                    with xfail_untranslated_messages(config, locale, msgids):
                        ins.assert_message_flashed(gettext(msgids[0]), "logo-error")
    finally:
        # Restore original image to logo location for subsequent tests
        with open(logo_image_location, "wb") as logo_file:
            logo_file.write(original_image)


def test_creation_of_ossec_test_log_event(journalist_app, test_admin, mocker):
    mocked_error_logger = mocker.patch("journalist.app.logger.error")
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )
        app.post(url_for("admin.ossec_test"))

    mocked_error_logger.assert_called_once_with("This is a test OSSEC alert")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_logo_upload_with_empty_input_field_fails(config, journalist_app, test_admin, locale):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )

        form = journalist_app_module.forms.LogoForm(logo=(BytesIO(b""), ""))

        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for("admin.manage_config", l=locale),
                data=form.data,
                follow_redirects=True,
            )

            assert page_language(resp.data) == language_tag(locale)
            msgids = ["File required."]
            with xfail_untranslated_messages(config, locale, msgids):
                ins.assert_message_flashed(gettext(msgids[0]), "logo-error")


def test_admin_page_restriction_http_gets(journalist_app, test_journo):
    admin_urls = [
        url_for("admin.index"),
        url_for("admin.add_user"),
        url_for("admin.edit_user", user_id=test_journo["id"]),
    ]

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )
        for admin_url in admin_urls:
            resp = app.get(admin_url)
            assert resp.status_code == 302


def test_admin_page_restriction_http_posts(journalist_app, test_journo):
    admin_urls = [
        url_for("admin.reset_two_factor_totp"),
        url_for("admin.reset_two_factor_hotp"),
        url_for("admin.add_user", user_id=test_journo["id"]),
        url_for("admin.new_user_two_factor"),
        url_for("admin.reset_two_factor_totp"),
        url_for("admin.reset_two_factor_hotp"),
        url_for("admin.edit_user", user_id=test_journo["id"]),
        url_for("admin.delete_user", user_id=test_journo["id"]),
    ]
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )
        for admin_url in admin_urls:
            resp = app.post(admin_url)
            assert resp.status_code == 302


def test_user_authorization_for_gets(journalist_app):
    urls = [
        url_for("main.index"),
        url_for("col.col", filesystem_id="1"),
        url_for("col.download_single_file", filesystem_id="1", fn="1"),
        url_for("account.edit"),
    ]

    with journalist_app.test_client() as app:
        for url in urls:
            resp = app.get(url)
            assert resp.status_code == 302


def test_user_authorization_for_posts(journalist_app):
    urls = [
        url_for("col.add_star", filesystem_id="1"),
        url_for("col.remove_star", filesystem_id="1"),
        url_for("col.process"),
        url_for("col.delete_single", filesystem_id="1"),
        url_for("main.reply"),
        url_for("main.bulk"),
        url_for("account.new_two_factor"),
        url_for("account.reset_two_factor_totp"),
        url_for("account.reset_two_factor_hotp"),
        url_for("account.change_name"),
    ]
    with journalist_app.test_client() as app:
        for url in urls:
            resp = app.post(url)
            assert resp.status_code == 302


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_incorrect_current_password_change(config, journalist_app, test_journo, locale):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )
        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for("account.new_password", l=locale),
                data=dict(password=VALID_PASSWORD, token="mocked", current_password="badpw"),
                follow_redirects=True,
            )
            assert page_language(resp.data) == language_tag(locale)
            msgids = [
                "Incorrect password or two-factor code.",
                (
                    "Please wait for a new code from your two-factor mobile"
                    " app or security key before trying again."
                ),
            ]
            with xfail_untranslated_messages(config, locale, msgids):
                ins.assert_message_flashed(gettext(msgids[0]) + " " + gettext(msgids[1]), "error")


# need a journalist app for the app context
def test_passphrase_migration_on_verification(journalist_app):
    salt = b64decode("+mGOQmD5Nnb+mH9gwBoxKRhKZmmJ6BzpmD5YArPHZsY=")
    journalist = Journalist("test", VALID_PASSWORD)

    # manually set the params
    hash = journalist._scrypt_hash(VALID_PASSWORD, salt)
    journalist.passphrase_hash = None
    journalist.pw_salt = salt
    journalist.pw_hash = hash

    assert journalist.valid_password(VALID_PASSWORD)

    # check that the migration happened
    assert journalist.passphrase_hash is not None
    assert journalist.passphrase_hash.startswith("$argon2")
    assert journalist.pw_salt is None
    assert journalist.pw_hash is None

    # check that a verification post-migration works
    assert journalist.valid_password(VALID_PASSWORD)


# need a journalist app for the app context
def test_passphrase_migration_on_reset(journalist_app):
    salt = b64decode("+mGOQmD5Nnb+mH9gwBoxKRhKZmmJ6BzpmD5YArPHZsY=")
    journalist = Journalist("test", VALID_PASSWORD)

    # manually set the params
    hash = journalist._scrypt_hash(VALID_PASSWORD, salt)
    journalist.passphrase_hash = None
    journalist.pw_salt = salt
    journalist.pw_hash = hash

    journalist.set_password(VALID_PASSWORD)

    # check that the migration happened
    assert journalist.passphrase_hash is not None
    assert journalist.passphrase_hash.startswith("$argon2")
    assert journalist.pw_salt is None
    assert journalist.pw_hash is None

    # check that a verification post-migration works
    assert journalist.valid_password(VALID_PASSWORD)


def test_passphrase_argon2i_migration(test_journo):
    """verify argon2i hashes work and then are migrated to argon2id"""
    journalist = test_journo["journalist"]
    # But use our password hash
    journalist.passphrase_hash = (
        "$argon2i$v=19$m=65536,t=4,p=2$JfFkLIJ2ogPUDI19XiBzHA$kaKNVckLLQNNBnmllMWqXg"
    )
    db.session.add(journalist)
    db.session.commit()
    assert journalist.valid_password("correct horse battery staple profanity oil chewy")
    assert journalist.passphrase_hash.startswith("$argon2id$")


def test_journalist_reply_view(journalist_app, test_source, test_journo, app_storage):
    source, _ = utils.db_helper.init_source(app_storage)
    journalist, _ = utils.db_helper.init_journalist()
    submissions = utils.db_helper.submit(app_storage, source, 1)
    replies = utils.db_helper.reply(app_storage, journalist, source, 1)

    subm_url = url_for(
        "col.download_single_file",
        filesystem_id=submissions[0].source.filesystem_id,
        fn=submissions[0].filename,
    )
    reply_url = url_for(
        "col.download_single_file",
        filesystem_id=replies[0].source.filesystem_id,
        fn=replies[0].filename,
    )

    with journalist_app.test_client() as app:
        resp = app.get(subm_url)
        assert resp.status_code == 302
        resp = app.get(reply_url)
        assert resp.status_code == 302


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_too_long_user_password_change(config, journalist_app, test_journo, locale):
    overly_long_password = VALID_PASSWORD + "a" * (
        Journalist.MAX_PASSWORD_LEN - len(VALID_PASSWORD) + 1
    )

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )

        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for("account.new_password", l=locale),
                data=dict(
                    password=overly_long_password,
                    token=TOTP(test_journo["otp_secret"]).now(),
                    current_password=test_journo["password"],
                ),
                follow_redirects=True,
            )

            assert page_language(resp.data) == language_tag(locale)
            msgids = ["The password you submitted is invalid. Password not changed."]
            with xfail_untranslated_messages(config, locale, msgids):
                ins.assert_message_flashed(gettext(msgids[0]), "error")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_valid_user_password_change(config, journalist_app, test_journo, locale):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )

        resp = app.post(
            url_for("account.new_password", l=locale),
            data=dict(
                password=VALID_PASSWORD_2,
                token=TOTP(test_journo["otp_secret"]).now(),
                current_password=test_journo["password"],
            ),
            follow_redirects=True,
        )

        assert page_language(resp.data) == language_tag(locale)
        msgids = [
            "Password updated. Don't forget to save it in your KeePassX database. New password:"
        ]
        with xfail_untranslated_messages(config, locale, msgids):
            assert escape(gettext(msgids[0])) in resp.data.decode("utf-8")


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_valid_user_first_last_name_change(config, journalist_app, test_journo, locale):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )

        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for("account.change_name", l=locale),
                data=dict(first_name="test", last_name="test"),
                follow_redirects=True,
            )

            assert page_language(resp.data) == language_tag(locale)
            msgids = ["Name updated.", "Name too long"]
            with xfail_untranslated_messages(config, locale, msgids):
                ins.assert_message_flashed(
                    gettext(msgids[0]).format(gettext("Name too long")), "success"
                )


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_valid_user_invalid_first_last_name_change(config, journalist_app, test_journo, locale):
    with journalist_app.test_client() as app:
        overly_long_name = "a" * (Journalist.MAX_NAME_LEN + 1)
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )

        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for("account.change_name", l=locale),
                data=dict(first_name=overly_long_name, last_name=overly_long_name),
                follow_redirects=True,
            )
            assert page_language(resp.data) == language_tag(locale)
            msgids = ["Name not updated: {message}", "Name too long"]
            with xfail_untranslated_messages(config, locale, msgids):
                ins.assert_message_flashed(
                    gettext(msgids[0]).format(message=gettext("Name too long")), "error"
                )


def test_regenerate_totp(journalist_app, test_journo):
    old_secret = test_journo["otp_secret"]

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )

        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(url_for("account.reset_two_factor_totp"))

            new_secret = Journalist.query.get(test_journo["id"]).otp_secret

            # check that totp is different
            assert new_secret != old_secret

            # should redirect to verification page
            ins.assert_redirects(resp, url_for("account.new_two_factor"))


def test_edit_hotp(journalist_app, test_journo):
    old_secret = test_journo["otp_secret"]
    valid_secret = "DEADBEEF01234567DEADBEEF01234567DADEFEEB"

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )

        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for("account.reset_two_factor_hotp"),
                data=dict(otp_secret=valid_secret),
            )

            new_secret = Journalist.query.get(test_journo["id"]).otp_secret

            # check that totp is different
            assert new_secret != old_secret

            # should redirect to verification page
            ins.assert_redirects(resp, url_for("account.new_two_factor"))


def test_delete_data_deletes_submissions_retaining_source(
    journalist_app, test_journo, test_source, app_storage
):
    """Verify that when only a source's data is deleted, the submissions
    are deleted but the source is not."""

    with journalist_app.app_context():
        source = Source.query.get(test_source["id"])
        journo = Journalist.query.get(test_journo["id"])

        utils.db_helper.submit(app_storage, source, 2)
        utils.db_helper.reply(app_storage, journo, source, 2)

        assert len(source.collection) == 4

        journalist_app_module.utils.delete_source_files(test_source["source"])

        res = Source.query.filter_by(id=test_source["id"]).one_or_none()
        assert res is not None

        assert len(source.collection) == 0


def test_bulk_delete_deletes_db_entries(
    journalist_app, test_source, test_journo, config, app_storage
):
    """
    Verify that when files are deleted, the corresponding db entries are
    also deleted.
    """

    with journalist_app.app_context():
        source = Source.query.get(test_source["id"])
        journo = Journalist.query.get(test_journo["id"])

        utils.db_helper.submit(app_storage, source, 2)
        utils.db_helper.reply(app_storage, journo, source, 2)

        dir_source_docs = os.path.join(config.STORE_DIR, test_source["filesystem_id"])
        assert os.path.exists(dir_source_docs)

        subs = Submission.query.filter_by(source_id=source.id).all()
        assert subs

        replies = Reply.query.filter_by(source_id=source.id).all()
        assert replies

        file_list = []
        file_list.extend(subs)
        file_list.extend(replies)

        with journalist_app.test_request_context("/"):
            journalist_app_module.utils.bulk_delete(test_source["filesystem_id"], file_list)

        def db_assertion():
            subs = Submission.query.filter_by(source_id=source.id).all()
            assert not subs

            replies = Reply.query.filter_by(source_id=source.id).all()
            assert not replies

        utils.asynchronous.wait_for_assertion(db_assertion)


def test_bulk_delete_works_when_files_absent(
    journalist_app, test_source, test_journo, config, app_storage
):
    """
    Verify that when files are deleted but are already missing,
    the corresponding db entries are still deleted
    """

    with journalist_app.app_context():
        source = Source.query.get(test_source["id"])
        journo = Journalist.query.get(test_journo["id"])

        utils.db_helper.submit(app_storage, source, 2)
        utils.db_helper.reply(app_storage, journo, source, 2)

        dir_source_docs = os.path.join(config.STORE_DIR, test_source["filesystem_id"])
        assert os.path.exists(dir_source_docs)

        subs = Submission.query.filter_by(source_id=source.id).all()
        assert subs

        replies = Reply.query.filter_by(source_id=source.id).all()
        assert replies

        file_list = []
        file_list.extend(subs)
        file_list.extend(replies)

        with journalist_app.test_request_context("/"):
            with patch("store.Storage.move_to_shredder") as delMock:
                delMock.side_effect = ValueError
                journalist_app_module.utils.bulk_delete(test_source["filesystem_id"], file_list)

        def db_assertion():
            subs = Submission.query.filter_by(source_id=source.id).all()
            assert not subs

            replies = Reply.query.filter_by(source_id=source.id).all()
            assert not replies

        utils.asynchronous.wait_for_assertion(db_assertion)


def test_login_with_invalid_password_doesnt_call_argon2(mocker, test_journo):
    mock_argon2 = mocker.patch("models.argon2.PasswordHasher")
    invalid_pw = "a" * (Journalist.MAX_PASSWORD_LEN + 1)

    with pytest.raises(InvalidPasswordLength):
        Journalist.login(test_journo["username"], invalid_pw, TOTP(test_journo["otp_secret"]).now())
    assert not mock_argon2.called


def test_render_locales(
    setup_journalist_key_and_gpg_folder: Tuple[str, Path],
    setup_rqworker: Tuple[str, str],
) -> None:
    """the locales.html template must collect both request.args (l=XX) and
    request.view_args (/<filesystem_id>) to build the URL to
    change the locale
    """
    journalist_key_fingerprint, gpg_key_dir = setup_journalist_key_and_gpg_folder
    worker_name, _ = setup_rqworker
    config_with_fr_locale = SecureDropConfigFactory.create(
        SECUREDROP_DATA_ROOT=Path(f"/tmp/sd-tests/render_locales"),
        GPG_KEY_DIR=gpg_key_dir,
        JOURNALIST_KEY=journalist_key_fingerprint,
        SUPPORTED_LOCALES=["en_US", "fr_FR"],
        RQ_WORKER_NAME=worker_name,
    )
    app = journalist_app_module.create_app(config_with_fr_locale)
    app.config["SERVER_NAME"] = "localhost.localdomain"  # needed for url_for
    with app.app_context():
        journo_user, journo_pw = utils.db_helper.init_journalist(is_admin=False)
        source_user = create_source_user(
            db_session=db.session,
            source_passphrase=PassphraseGenerator.get_default().generate_passphrase(),
            source_app_storage=Storage(
                str(config_with_fr_locale.STORE_DIR), str(config_with_fr_locale.TEMP_DIR)
            ),
        )

        url = url_for("col.col", filesystem_id=source_user.filesystem_id)
        # we need the relative URL, not the full url including proto / localhost
        url_end = url.replace("http://", "")
        url_end = url_end[url_end.index("/") + 1 :]

        with app.test_client() as app:
            login_journalist(app, journo_user.username, journo_pw, journo_user.otp_secret)
            resp = app.get(url + "?l=fr_FR")

        # check that links to i18n URLs are/aren't present
        text = resp.data.decode("utf-8")
        assert "?l=fr_FR" not in text, text
        assert url_end + "?l=en_US" in text, text


def test_download_selected_submissions_and_replies(
    journalist_app, test_journo, test_source, app_storage
):
    journo = Journalist.query.get(test_journo["id"])
    source = Source.query.get(test_source["id"])
    submissions = utils.db_helper.submit(app_storage, source, 4)
    replies = utils.db_helper.reply(app_storage, journo, source, 4)
    selected_submissions = random.sample(submissions, 2)
    selected_replies = random.sample(replies, 2)
    selected = [submission.filename for submission in selected_submissions + selected_replies]
    selected.sort()

    with journalist_app.test_client() as app:
        login_journalist(app, journo.username, test_journo["password"], test_journo["otp_secret"])
        resp = app.post(
            "/bulk",
            data=dict(
                action="download",
                filesystem_id=test_source["filesystem_id"],
                doc_names_selected=selected,
            ),
        )

    # The download request was succesful, and the app returned a zipfile
    assert resp.status_code == 200
    assert resp.content_type == "application/zip"
    assert zipfile.is_zipfile(BytesIO(resp.data))

    # The items selected are in the zipfile and items are marked seen
    for item in selected_submissions + selected_replies:
        zipinfo = zipfile.ZipFile(BytesIO(resp.data)).getinfo(
            os.path.join(
                source.journalist_filename,
                "{}_{}".format(item.filename.split("-")[0], source.last_updated.date()),
                item.filename,
            )
        )
        assert zipinfo

        seen_file = SeenFile.query.filter_by(file_id=item.id, journalist_id=journo.id).one_or_none()
        seen_message = SeenMessage.query.filter_by(
            message_id=item.id, journalist_id=journo.id
        ).one_or_none()
        seen_reply = SeenReply.query.filter_by(
            reply_id=item.id, journalist_id=journo.id
        ).one_or_none()

        if not seen_file and not seen_message and not seen_reply:
            assert False

    # The items not selected are absent from the zipfile
    not_selected_submissions = set(submissions).difference(selected_submissions)
    not_selected_replies = set(replies).difference(selected_replies)
    not_selected = [i.filename for i in not_selected_submissions.union(not_selected_replies)]
    for filename in not_selected:
        with pytest.raises(KeyError):
            zipfile.ZipFile(BytesIO(resp.data)).getinfo(
                os.path.join(
                    source.journalist_filename,
                    source.journalist_designation,
                    "{}_{}".format(filename.split("-")[0], source.last_updated.date()),
                    filename,
                )
            )


def test_download_selected_submissions_and_replies_previously_seen(
    journalist_app, test_journo, test_source, app_storage
):
    journo = Journalist.query.get(test_journo["id"])
    source = Source.query.get(test_source["id"])
    submissions = utils.db_helper.submit(app_storage, source, 4)
    replies = utils.db_helper.reply(app_storage, journo, source, 4)
    selected_submissions = random.sample(submissions, 2)
    selected_replies = random.sample(replies, 2)
    selected = [submission.filename for submission in selected_submissions + selected_replies]
    selected.sort()

    # Mark selected files, messages, and replies as seen
    seen_file = SeenFile(file_id=selected_submissions[0].id, journalist_id=journo.id)
    db.session.add(seen_file)
    seen_message = SeenMessage(message_id=selected_submissions[1].id, journalist_id=journo.id)
    db.session.add(seen_message)
    mark_seen(selected_replies, journo)
    db.session.commit()

    with journalist_app.test_client() as app:
        login_journalist(app, journo.username, test_journo["password"], test_journo["otp_secret"])
        resp = app.post(
            "/bulk",
            data=dict(
                action="download",
                filesystem_id=test_source["filesystem_id"],
                doc_names_selected=selected,
            ),
        )

    # The download request was succesful, and the app returned a zipfile
    assert resp.status_code == 200
    assert resp.content_type == "application/zip"
    assert zipfile.is_zipfile(BytesIO(resp.data))

    # The items selected are in the zipfile and items are marked seen
    for item in selected_submissions + selected_replies:
        zipinfo = zipfile.ZipFile(BytesIO(resp.data)).getinfo(
            os.path.join(
                source.journalist_filename,
                "{}_{}".format(item.filename.split("-")[0], source.last_updated.date()),
                item.filename,
            )
        )
        assert zipinfo

        seen_file = SeenFile.query.filter_by(file_id=item.id, journalist_id=journo.id).one_or_none()
        seen_message = SeenMessage.query.filter_by(
            message_id=item.id, journalist_id=journo.id
        ).one_or_none()
        seen_reply = SeenReply.query.filter_by(
            reply_id=item.id, journalist_id=journo.id
        ).one_or_none()

        if not seen_file and not seen_message and not seen_reply:
            assert False

    # The items not selected are absent from the zipfile
    not_selected_submissions = set(submissions).difference(selected_submissions)
    not_selected_replies = set(replies).difference(selected_replies)
    not_selected = [i.filename for i in not_selected_submissions.union(not_selected_replies)]
    for filename in not_selected:
        with pytest.raises(KeyError):
            zipfile.ZipFile(BytesIO(resp.data)).getinfo(
                os.path.join(
                    source.journalist_filename,
                    source.journalist_designation,
                    "{}_{}".format(filename.split("-")[0], source.last_updated.date()),
                    filename,
                )
            )


def test_download_selected_submissions_previously_downloaded(
    journalist_app, test_journo, test_source, app_storage
):
    journo = Journalist.query.get(test_journo["id"])
    source = Source.query.get(test_source["id"])
    submissions = utils.db_helper.submit(app_storage, source, 4)
    replies = utils.db_helper.reply(app_storage, journo, source, 4)
    selected_submissions = random.sample(submissions, 2)
    selected_replies = random.sample(replies, 2)
    selected = [submission.filename for submission in selected_submissions + selected_replies]
    selected.sort()

    # Mark selected submissions as downloaded
    for submission in selected_submissions:
        submission.downloaded = True
        db.session.commit()

    with journalist_app.test_client() as app:
        login_journalist(app, journo.username, test_journo["password"], test_journo["otp_secret"])
        resp = app.post(
            "/bulk",
            data=dict(
                action="download",
                filesystem_id=test_source["filesystem_id"],
                doc_names_selected=selected,
            ),
        )

    # The download request was succesful, and the app returned a zipfile
    assert resp.status_code == 200
    assert resp.content_type == "application/zip"
    assert zipfile.is_zipfile(BytesIO(resp.data))

    # The items selected are in the zipfile
    for filename in selected:
        zipinfo = zipfile.ZipFile(BytesIO(resp.data)).getinfo(
            os.path.join(
                source.journalist_filename,
                "{}_{}".format(filename.split("-")[0], source.last_updated.date()),
                filename,
            )
        )
        assert zipinfo

    # The items not selected are absent from the zipfile
    not_selected_submissions = set(submissions).difference(selected_submissions)
    not_selected_replies = set(replies).difference(selected_replies)
    not_selected = [i.filename for i in not_selected_submissions.union(not_selected_replies)]
    for filename in not_selected:
        with pytest.raises(KeyError):
            zipfile.ZipFile(BytesIO(resp.data)).getinfo(
                os.path.join(
                    source.journalist_filename,
                    source.journalist_designation,
                    "{}_{}".format(filename.split("-")[0], source.last_updated.date()),
                    filename,
                )
            )


@pytest.fixture(scope="function")
def selected_missing_files(journalist_app, test_source, app_storage):
    """Fixture for the download tests with missing files in storage."""
    source = Source.query.get(test_source["id"])
    submissions = utils.db_helper.submit(app_storage, source, 2)
    selected = sorted([s.filename for s in submissions])

    storage_path = Path(app_storage.storage_path)
    msg_files = sorted([p for p in storage_path.rglob("*") if p.is_file()])
    assert len(msg_files) == 2
    for file in msg_files:
        file.unlink()

    yield selected


def test_download_selected_submissions_missing_files(
    journalist_app,
    test_journo,
    test_source,
    mocker,
    selected_missing_files,
    app_storage,
):
    """Tests download of selected submissions with missing files in storage."""
    mocked_error_logger = mocker.patch("journalist.app.logger.error")
    journo = Journalist.query.get(test_journo["id"])

    with journalist_app.test_client() as app:
        login_journalist(app, journo.username, test_journo["password"], test_journo["otp_secret"])
        resp = app.post(
            url_for("main.bulk"),
            data=dict(
                action="download",
                filesystem_id=test_source["filesystem_id"],
                doc_names_selected=selected_missing_files,
            ),
        )

    assert resp.status_code == 302

    expected_calls = []
    for file in selected_missing_files:
        missing_file = (
            Path(app_storage.storage_path)
            .joinpath(test_source["filesystem_id"])
            .joinpath(file)
            .as_posix()
        )
        expected_calls.append(call(f"File {missing_file} not found"))

    mocked_error_logger.assert_has_calls(expected_calls)


def test_download_single_submission_missing_file(
    journalist_app,
    test_journo,
    test_source,
    mocker,
    selected_missing_files,
    app_storage,
):
    """Tests download of single submissions with missing files in storage."""
    mocked_error_logger = mocker.patch("journalist.app.logger.error")
    journo = Journalist.query.get(test_journo["id"])
    missing_file = selected_missing_files[0]

    with journalist_app.test_client() as app:
        login_journalist(app, journo.username, test_journo["password"], test_journo["otp_secret"])
        resp = app.get(
            url_for(
                "col.download_single_file",
                filesystem_id=test_source["filesystem_id"],
                fn=missing_file,
            )
        )

    assert resp.status_code == 302

    missing_file = (
        Path(app_storage.storage_path)
        .joinpath(test_source["filesystem_id"])
        .joinpath(missing_file)
        .as_posix()
    )

    mocked_error_logger.assert_called_once_with(f"File {missing_file} not found")


def test_download_unread_all_sources(journalist_app, test_journo, app_storage):
    """
    Test that downloading all unread creates a zip that contains all unread submissions from the
    selected sources and marks these submissions as seen.
    """
    journo = Journalist.query.get(test_journo["id"])

    bulk = utils.db_helper.bulk_setup_for_seen_only(journo, app_storage)

    with journalist_app.test_client() as app:
        login_journalist(app, journo.username, test_journo["password"], test_journo["otp_secret"])

        # Select all sources supplied from bulk_download_setup
        selected = []
        for i in bulk:
            source = i["source"]
            selected.append(source.filesystem_id)

        # Download all unread submissions (not replies) from all sources selected
        resp = app.post(
            url_for("col.process"),
            data=dict(action="download-unread", cols_selected=selected),
        )

    # The download request was succesful, and the app returned a zipfile
    assert resp.status_code == 200
    assert resp.content_type == "application/zip"
    assert zipfile.is_zipfile(BytesIO(resp.data))

    for i in bulk:
        source = i["source"]
        seen_files = i["seen_files"]
        seen_messages = i["seen_messages"]
        seen_replies = i["seen_replies"]
        unseen_files = i["unseen_files"]
        unseen_messages = i["unseen_messages"]
        unseen_replies = i["unseen_replies"]
        not_downloaded = i["not_downloaded"]

        # Check that the zip file contains all submissions for the source that haven't been marked
        # as downloaded and that they are now marked as seen in the database
        for item in not_downloaded + unseen_files + unseen_messages:
            zipinfo = zipfile.ZipFile(BytesIO(resp.data)).getinfo(
                os.path.join(
                    "unread",
                    source.journalist_designation,
                    "{}_{}".format(item.filename.split("-")[0], source.last_updated.date()),
                    item.filename,
                )
            )
            assert zipinfo

            seen_file = SeenFile.query.filter_by(
                file_id=item.id, journalist_id=journo.id
            ).one_or_none()
            seen_message = SeenMessage.query.filter_by(
                message_id=item.id, journalist_id=journo.id
            ).one_or_none()

            if not seen_file and not seen_message:
                assert False

        # Check that the zip file does not contain any seen data or replies
        for item in seen_files + seen_messages + seen_replies + unseen_replies:
            with pytest.raises(KeyError):
                zipinfo = zipfile.ZipFile(BytesIO(resp.data)).getinfo(
                    os.path.join(
                        "unread",
                        source.journalist_designation,
                        "{}_{}".format(item.filename.split("-")[0], source.last_updated.date()),
                        item.filename,
                    )
                )
                assert zipinfo


def test_download_all_selected_sources(journalist_app, test_journo, app_storage):
    """
    Test that downloading all selected sources creates zip that contains all submissions from the
    selected sources and marks these submissions as seen.
    """
    journo = Journalist.query.get(test_journo["id"])

    bulk = utils.db_helper.bulk_setup_for_seen_only(journo, app_storage)

    with journalist_app.test_client() as app:
        login_journalist(app, journo.username, test_journo["password"], test_journo["otp_secret"])

        # Select all sources supplied from bulk_download_setup
        selected = []
        for i in bulk:
            source = i["source"]
            selected.append(source.filesystem_id)

        # Download all submissions from all sources selected
        resp = app.post(
            url_for("col.process"),
            data=dict(action="download-all", cols_selected=selected),
        )

    # The download request was succesful, and the app returned a zipfile
    assert resp.status_code == 200
    assert resp.content_type == "application/zip"
    assert zipfile.is_zipfile(BytesIO(resp.data))

    for i in bulk:
        source = i["source"]
        seen_files = i["seen_files"]
        seen_messages = i["seen_messages"]
        seen_replies = i["seen_replies"]
        unseen_files = i["unseen_files"]
        unseen_messages = i["unseen_messages"]
        unseen_replies = i["unseen_replies"]
        not_downloaded = i["not_downloaded"]

        # Check that the zip file contains all submissions for the source
        for item in not_downloaded + unseen_files + unseen_messages + seen_files + seen_messages:
            zipinfo = zipfile.ZipFile(BytesIO(resp.data)).getinfo(
                os.path.join(
                    "all",
                    source.journalist_designation,
                    "{}_{}".format(item.filename.split("-")[0], source.last_updated.date()),
                    item.filename,
                )
            )
            assert zipinfo

            seen_file = SeenFile.query.filter_by(
                file_id=item.id, journalist_id=journo.id
            ).one_or_none()
            seen_message = SeenMessage.query.filter_by(
                message_id=item.id, journalist_id=journo.id
            ).one_or_none()

            if not seen_file and not seen_message:
                assert False

        # Check that the zip file does not contain any replies
        for item in seen_replies + unseen_replies:
            with pytest.raises(KeyError):
                zipinfo = zipfile.ZipFile(BytesIO(resp.data)).getinfo(
                    os.path.join(
                        "unread",
                        source.journalist_designation,
                        "{}_{}".format(item.filename.split("-")[0], source.last_updated.date()),
                        item.filename,
                    )
                )
                assert zipinfo


def test_single_source_is_successfully_starred(journalist_app, test_journo, test_source):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )
        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(url_for("col.add_star", filesystem_id=test_source["filesystem_id"]))

            ins.assert_redirects(resp, url_for("main.index"))

    source = Source.query.get(test_source["id"])
    assert source.star.starred


def test_single_source_is_successfully_unstarred(journalist_app, test_journo, test_source):
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )
        # First star the source
        app.post(url_for("col.add_star", filesystem_id=test_source["filesystem_id"]))

        with InstrumentedApp(journalist_app) as ins:
            # Now unstar the source
            resp = app.post(url_for("col.remove_star", filesystem_id=test_source["filesystem_id"]))

            ins.assert_redirects(resp, url_for("main.index"))

        source = Source.query.get(test_source["id"])
        assert not source.star.starred


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_journalist_session_expiration(journalist_app, test_journo, locale):
    # set the expiration to be very short
    journalist_app.session_interface.lifetime = 1
    with journalist_app.test_client() as app:
        with InstrumentedApp(journalist_app) as ins:
            login_data = {
                "username": test_journo["username"],
                "password": test_journo["password"],
                "token": TOTP(test_journo["otp_secret"]).now(),
            }
            resp = app.post(url_for("main.login"), data=login_data)
            ins.assert_redirects(resp, url_for("main.index"))
        assert "uid" in session

        # Wait 2s for the redis key to expire
        time.sleep(2)
        resp = app.get(url_for("account.edit"), follow_redirects=True)
        # because the session is being cleared when it expires, the
        # response should always be in English.
        assert page_language(resp.data) == "en-US"
        assert "Login to access the journalist interface" in resp.data.decode("utf-8")

        # check that the session was cleared (apart from 'expires'
        # which is always present and 'csrf_token' which leaks no info)
        session.pop("expires", None)
        session.pop("csrf_token", None)
        session.pop("locale", None)
        session.pop("renew_count", None)
        assert not session, session


@flaky(rerun_filter=utils.flaky_filter_xfail)
@pytest.mark.parametrize("locale", get_test_locales())
def test_csrf_error_page(config, journalist_app, locale):
    # get the locale into the session
    with journalist_app.test_client() as app:
        resp = app.get(url_for("main.login", l=locale))
        assert page_language(resp.data) == language_tag(locale)
        msgids = ["Show password"]
        with xfail_untranslated_messages(config, locale, msgids):
            assert gettext(msgids[0]) in resp.data.decode("utf-8")

    journalist_app.config["WTF_CSRF_ENABLED"] = True
    with journalist_app.test_client() as app:
        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(url_for("main.login"))
            ins.assert_redirects(resp, url_for("main.login"))

        resp = app.post(url_for("main.login"), follow_redirects=True)

        # because the session is being cleared when it expires, the
        # response should always be in English.
        assert page_language(resp.data) == "en-US"
        assert "You have been logged out due to inactivity." in resp.data.decode("utf-8")


def test_col_process_aborts_with_bad_action(journalist_app, test_journo):
    """If the action is not a valid choice, a 500 should occur"""
    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )

        form_data = {
            "cols_selected": "does not matter",
            "action": "this action does not exist",
        }

        resp = app.post(url_for("col.process"), data=form_data)
        assert resp.status_code == 500


def test_col_process_successfully_deletes_multiple_sources(
    journalist_app, test_journo, app_storage
):
    # Create two sources with one submission each
    source_1, _ = utils.db_helper.init_source(app_storage)
    utils.db_helper.submit(app_storage, source_1, 1)
    source_2, _ = utils.db_helper.init_source(app_storage)
    utils.db_helper.submit(app_storage, source_2, 1)
    source_3, _ = utils.db_helper.init_source(app_storage)
    utils.db_helper.submit(app_storage, source_3, 1)

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )

        form_data = {
            "cols_selected": [source_1.filesystem_id, source_2.filesystem_id],
            "action": "delete",
        }

        resp = app.post(url_for("col.process"), data=form_data, follow_redirects=True)

        assert resp.status_code == 200

    # simulate the source_deleter's work
    journalist_app_module.utils.purge_deleted_sources()

    # Verify that all of the specified sources were deleted, but no others
    remaining_sources = Source.query.all()
    assert len(remaining_sources) == 1
    assert remaining_sources[0].uuid == source_3.uuid


def test_col_process_successfully_stars_sources(
    journalist_app, test_journo, test_source, app_storage
):
    utils.db_helper.submit(app_storage, test_source["source"], 1)

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )

        form_data = {"cols_selected": [test_source["filesystem_id"]], "action": "star"}

        resp = app.post(url_for("col.process"), data=form_data, follow_redirects=True)
        assert resp.status_code == 200

    source = Source.query.get(test_source["id"])
    assert source.star.starred


def test_col_process_successfully_unstars_sources(
    journalist_app, test_journo, test_source, app_storage
):
    utils.db_helper.submit(app_storage, test_source["source"], 1)

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )

        # First star the source
        form_data = {"cols_selected": [test_source["filesystem_id"]], "action": "star"}
        app.post(url_for("col.process"), data=form_data, follow_redirects=True)

        # Now unstar the source
        form_data = {
            "cols_selected": [test_source["filesystem_id"]],
            "action": "un-star",
        }
        resp = app.post(url_for("col.process"), data=form_data, follow_redirects=True)

    assert resp.status_code == 200

    source = Source.query.get(test_source["id"])
    assert not source.star.starred


def test_source_with_null_last_updated(journalist_app, test_journo, test_files):
    """Regression test for issues #3862"""

    source = test_files["source"]
    source.last_updated = None
    db.session.add(source)
    db.session.commit()

    with journalist_app.test_client() as app:
        login_journalist(
            app,
            test_journo["username"],
            test_journo["password"],
            test_journo["otp_secret"],
        )
        resp = app.get(url_for("main.index"))
        assert resp.status_code == 200


def test_does_set_cookie_headers(journalist_app, test_journo):
    with journalist_app.test_client() as app:
        response = app.get(url_for("main.login"))

        observed_headers = response.headers
        assert "Set-Cookie" in list(observed_headers.keys())
        assert "Cookie" in observed_headers["Vary"]


def test_app_error_handlers_defined(journalist_app):
    for status_code in [400, 401, 403, 404, 500]:
        # This will raise KeyError if an app-wide error handler is not defined
        assert journalist_app.error_handler_spec[None][status_code]


def test_lazy_deleted_journalist_creation(journalist_app):
    """test lazy creation of "deleted" journalist works"""
    not_found = Journalist.query.filter_by(username="deleted").one_or_none()
    assert not_found is None, "deleted journalist doesn't exist yet"
    deleted = Journalist.get_deleted()
    db.session.commit()
    # Can be found as a normal Journalist object
    found = Journalist.query.filter_by(username="deleted").one()
    assert deleted.uuid == found.uuid
    assert found.is_deleted_user() is True
    # And get_deleted() now returns the same instance
    deleted2 = Journalist.get_deleted()
    assert deleted.uuid == deleted2.uuid


def test_journalist_deletion(journalist_app, app_storage):
    """test deleting a journalist and see data reassociated to "deleted" journalist"""
    # Create a journalist that's seen two replies and has a login attempt
    source, _ = utils.db_helper.init_source(app_storage)
    journalist, _ = utils.db_helper.init_journalist()
    db.session.add(JournalistLoginAttempt(journalist))
    replies = utils.db_helper.reply(app_storage, journalist, source, 2)
    # Create a second journalist that's seen those replies
    journalist2, _ = utils.db_helper.init_journalist()
    for reply in replies:
        db.session.add(SeenReply(reply=reply, journalist=journalist2))
    db.session.commit()
    # Only one login attempt in the table
    assert len(JournalistLoginAttempt.query.all()) == 1
    # And four SeenReply instances
    assert len(SeenReply.query.all()) == 4
    # Delete the journalists
    journalist.delete()
    journalist2.delete()
    db.session.commit()
    # Verify the "deleted" journalist has 2 associated rows of both types
    deleted = Journalist.get_deleted()
    assert len(Reply.query.filter_by(journalist_id=deleted.id).all()) == 2
    assert len(SeenReply.query.filter_by(journalist_id=deleted.id).all()) == 2
    # And there are no login attempts
    assert JournalistLoginAttempt.query.all() == []
