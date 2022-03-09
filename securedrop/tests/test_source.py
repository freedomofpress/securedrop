# -*- coding: utf-8 -*-
# flake8: noqa: E741
import gzip
import re
import subprocess
import time
import os
import shutil
from datetime import datetime, timedelta, timezone
from io import BytesIO, StringIO
from pathlib import Path
from unittest import mock

from flaky import flaky
from flask import session, escape, url_for, g, request
from flask_babel import gettext
from mock import patch, ANY
import pytest

from passphrases import PassphraseGenerator
from source_app.session_manager import SessionManager
from . import utils
import version

from db import db
from journalist_app.utils import delete_collection
from models import InstanceConfig, Source, Reply
from source_app import api as source_app_api, session_manager
from source_app import get_logo_url
from .utils.db_helper import new_codename, submit
from .utils.i18n import get_test_locales, language_tag, page_language, xfail_untranslated_messages
from .utils.instrument import InstrumentedApp

GENERATE_DATA = {'tor2web_check': 'href="fake.onion"'}


def test_logo_default_available(config, source_app):
    # if the custom image is available, this test will fail
    custom_image_location = os.path.join(
        config.SECUREDROP_ROOT, "static/i/custom_logo.png"
    )
    if os.path.exists(custom_image_location):
        os.remove(custom_image_location)

    with source_app.test_client() as app:
        logo_url = get_logo_url(source_app)
        assert logo_url.endswith('i/logo.png')
        response = app.get(logo_url, follow_redirects=False)
        assert response.status_code == 200


def test_logo_custom_available(config, source_app):
    # if the custom image is available, this test will fail
    custom_image = os.path.join(config.SECUREDROP_ROOT, "static/i/custom_logo.png")
    default_image = os.path.join(config.SECUREDROP_ROOT, "static/i/logo.png")
    if os.path.exists(default_image) and not os.path.exists(custom_image):
        shutil.copyfile(default_image, custom_image)

    with source_app.test_client() as app:
        logo_url = get_logo_url(source_app)
        assert logo_url.endswith('i/custom_logo.png')
        response = app.get(logo_url, follow_redirects=False)
        assert response.status_code == 200


def test_page_not_found(source_app):
    """Verify the page not found condition returns the intended template"""
    with InstrumentedApp(source_app) as ins:
        with source_app.test_client() as app:
            resp = app.get('UNKNOWN')
            assert resp.status_code == 404
            ins.assert_template_used('notfound.html')


def test_orgname_default_set(source_app):

    class dummy_current():
        organization_name = None

    with patch.object(InstanceConfig, 'get_current') as iMock:
        with source_app.test_client() as app:
            iMock.return_value = dummy_current()
            resp = app.get(url_for('main.index'))
            assert resp.status_code == 200
            assert g.organization_name == "SecureDrop"


def test_index(source_app):
    """Test that the landing page loads and looks how we expect"""
    with source_app.test_client() as app:
        resp = app.get(url_for('main.index'))
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert 'First submission' in text
        assert 'Return visit' in text


def _find_codename(html):
    """Find a source codename (diceware passphrase) in HTML"""
    # Codenames may contain HTML escape characters, and the wordlist
    # contains various symbols.
    codename_re = (r'<mark [^>]*id="codename"[^>]*>'
                   r'(?P<codename>[a-z0-9 &#;?:=@_.*+()\'"$%!-]+)</mark>')
    codename_match = re.search(codename_re, html)
    assert codename_match is not None
    return codename_match.group('codename')


def test_generate_already_logged_in(source_app):
    with source_app.test_client() as app:
        new_codename(app, session)
        # Make sure it redirects to /lookup when logged in
        resp = app.post(url_for('main.generate'), data=GENERATE_DATA)
        assert resp.status_code == 302
        # Make sure it flashes the message on the lookup page
        resp = app.post(url_for('main.generate'), data=GENERATE_DATA, follow_redirects=True)
        # Should redirect to /lookup
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "because you are already logged in." in text


def test_create_new_source(source_app):
    with source_app.test_client() as app:
        resp = app.post(url_for('main.generate'), data=GENERATE_DATA)
        assert resp.status_code == 200
        tab_id = next(iter(session['codenames'].keys()))
        resp = app.post(url_for('main.create'), data={'tab_id': tab_id}, follow_redirects=True)
        assert SessionManager.is_user_logged_in(db_session=db.session)
        # should be redirected to /lookup
        text = resp.data.decode('utf-8')
        assert "Submit Files" in text
        assert 'codenames' not in session


def test_generate(source_app):
    with source_app.test_client() as app:
        resp = app.post(url_for('main.generate'), data=GENERATE_DATA)
        assert resp.status_code == 200
        session_codename = next(iter(session['codenames'].values()))

    text = resp.data.decode('utf-8')
    assert "functions as both your username and your password" in text

    codename = _find_codename(resp.data.decode('utf-8'))
    # codename is also stored in the session - make sure it matches the
    # codename displayed to the source
    assert codename == escape(session_codename)


def test_create_duplicate_codename_logged_in_not_in_session(source_app):
    with patch.object(source_app.logger, 'error') as logger:
        with source_app.test_client() as app:
            resp = app.post(url_for('main.generate'), data=GENERATE_DATA)
            assert resp.status_code == 200
            tab_id, codename = next(iter(session['codenames'].items()))

            # Create a source the first time
            resp = app.post(url_for('main.create'), data={'tab_id': tab_id}, follow_redirects=True)
            assert resp.status_code == 200

        with source_app.test_client() as app:
            # Attempt to add the same source
            with app.session_transaction() as sess:
                sess['codenames'] = {tab_id: codename}
                sess["codenames_expire"] = datetime.utcnow() + timedelta(hours=1)
            resp = app.post(url_for('main.create'), data={'tab_id': tab_id}, follow_redirects=True)
            logger.assert_called_once()
            assert "Could not create a source" in logger.call_args[0][0]
            assert resp.status_code == 200
            assert not SessionManager.is_user_logged_in(db_session=db.session)


def test_create_duplicate_codename_logged_in_in_session(source_app):
    with source_app.test_client() as app:
        # Given a user who generated a codename in a browser tab
        resp = app.post(url_for('main.generate'), data=GENERATE_DATA)
        assert resp.status_code == 200
        first_tab_id, first_codename = list(session['codenames'].items())[0]

        # And then they opened a new browser tab to generate a second codename
        resp = app.post(url_for('main.generate'), data=GENERATE_DATA)
        assert resp.status_code == 200
        second_tab_id, second_codename = list(session['codenames'].items())[1]
        assert first_codename != second_codename

        # And the user then completed the account creation flow in the first tab
        resp = app.post(
            url_for('main.create'), data={'tab_id': first_tab_id}, follow_redirects=True
        )
        assert resp.status_code == 200
        first_tab_account = SessionManager.get_logged_in_user(db_session=db.session)

        # When the user tries to complete the account creation flow again, in the second tab
        resp = app.post(
            url_for('main.create'), data={'tab_id': second_tab_id}, follow_redirects=True
        )

        # Then the user is shown the "already logged in" message
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "You are already logged in." in text

        # And no new account was created
        second_tab_account = SessionManager.get_logged_in_user(db_session=db.session)
        assert second_tab_account.filesystem_id == first_tab_account.filesystem_id


def test_lookup(source_app):
    """Test various elements on the /lookup page."""
    with source_app.test_client() as app:
        codename = new_codename(app, session)
        resp = app.post(url_for('main.login'), data=dict(codename=codename),
                        follow_redirects=True)
        # redirects to /lookup
        text = resp.data.decode('utf-8')
        assert "public key" in text
        # download the public key
        resp = app.get(url_for('info.download_public_key'))
        text = resp.data.decode('utf-8')
        assert "BEGIN PGP PUBLIC KEY BLOCK" in text


def test_journalist_key_redirects_to_public_key(source_app):
    """Test that the /journalist-key route redirects to /public-key."""
    with source_app.test_client() as app:
        resp = app.get(url_for('info.download_journalist_key'))
        assert resp.status_code == 301
        resp = app.get(url_for('info.download_journalist_key'), follow_redirects=True)
        assert request.path == url_for('info.download_public_key')
        assert "BEGIN PGP PUBLIC KEY BLOCK" in resp.data.decode('utf-8')


def test_login_and_logout(source_app):
    with source_app.test_client() as app:
        resp = app.get(url_for('main.login'))
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Enter Codename" in text

        codename = new_codename(app, session)
        resp = app.post(url_for('main.login'),
                        data=dict(codename=codename),
                        follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Submit Files" in text
        assert SessionManager.is_user_logged_in(db_session=db.session)

    with source_app.test_client() as app:
        resp = app.post(url_for('main.login'),
                        data=dict(codename='invalid'),
                        follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert 'Sorry, that is not a recognized codename.' in text
        assert not SessionManager.is_user_logged_in(db_session=db.session)

    with source_app.test_client() as app:
        resp = app.post(url_for('main.login'),
                        data=dict(codename=codename),
                        follow_redirects=True)
        assert resp.status_code == 200
        assert SessionManager.is_user_logged_in(db_session=db.session)

        resp = app.post(url_for('main.login'),
                        data=dict(codename=codename),
                        follow_redirects=True)
        assert resp.status_code == 200
        assert SessionManager.is_user_logged_in(db_session=db.session)

        resp = app.get(url_for('main.logout'),
                       follow_redirects=True)
        assert not SessionManager.is_user_logged_in(db_session=db.session)
        text = resp.data.decode('utf-8')

        # This is part of the logout page message instructing users
        # to click the 'New Identity' icon
        assert 'This will clear your Tor Browser activity data' in text


def test_user_must_log_in_for_protected_views(source_app):
    with source_app.test_client() as app:
        resp = app.get(url_for('main.lookup'),
                       follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Enter Codename" in text


def test_login_with_whitespace(source_app):
    """
    Test that codenames with leading or trailing whitespace still work
    """

    def login_test(app, codename):
        resp = app.get(url_for('main.login'))
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Enter Codename" in text

        resp = app.post(url_for('main.login'),
                        data=dict(codename=codename),
                        follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Submit Files" in text
        assert SessionManager.is_user_logged_in(db_session=db.session)

    with source_app.test_client() as app:
        codename = new_codename(app, session)

    codenames = [
        codename + ' ',
        ' ' + codename + ' ',
        ' ' + codename,
    ]

    for codename_ in codenames:
        with source_app.test_client() as app:
            login_test(app, codename_)


def test_login_with_missing_reply_files(source_app, app_storage):
    """
    Test that source can log in when replies are present in database but missing
    from storage.
    """
    source, codename = utils.db_helper.init_source(app_storage)
    journalist, _ = utils.db_helper.init_journalist()
    replies = utils.db_helper.reply(app_storage, journalist, source, 1)
    assert len(replies) > 0
    # Delete the reply file
    reply_file_path = Path(app_storage.path(source.filesystem_id, replies[0].filename))
    reply_file_path.unlink()
    assert not reply_file_path.exists()

    with source_app.test_client() as app:
        resp = app.get(url_for('main.login'))
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Enter Codename" in text

        resp = app.post(url_for('main.login'),
                        data=dict(codename=codename),
                        follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Submit Files" in text
        assert SessionManager.is_user_logged_in(db_session=db.session)


def _dummy_submission(app):
    """
    Helper to make a submission (content unimportant), mostly useful in
    testing notification behavior for a source's first vs. their
    subsequent submissions
    """
    return app.post(
        url_for('main.submit'),
        data=dict(msg="Pay no attention to the man behind the curtain.",
                  fh=(BytesIO(b''), '')),
        follow_redirects=True)


def test_initial_submission_notification(source_app):
    """
    Regardless of the type of submission (message, file, or both), the
    first submission is always greeted with a notification
    reminding sources to check back later for replies.
    """
    with source_app.test_client() as app:
        new_codename(app, session)
        resp = _dummy_submission(app)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Thank you for sending this information to us." in text


def test_submit_message(source_app):
    with source_app.test_client() as app:
        new_codename(app, session)
        _dummy_submission(app)
        resp = app.post(
            url_for('main.submit'),
            data=dict(msg="This is a test.", fh=(StringIO(''), '')),
            follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Thanks! We received your message" in text


def test_submit_empty_message(source_app):
    with source_app.test_client() as app:
        new_codename(app, session)
        resp = app.post(
            url_for('main.submit'),
            data=dict(msg="", fh=(StringIO(''), '')),
            follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "You must enter a message or choose a file to submit." \
            in text


def test_submit_big_message(source_app):
    """
    Test the message size limit.
    """
    with source_app.test_client() as app:
        new_codename(app, session)
        _dummy_submission(app)
        resp = app.post(
            url_for('main.submit'),
            data=dict(msg="AA" * (1024 * 512), fh=(StringIO(''), '')),
            follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Message text too long." in text


def test_submit_initial_short_message(source_app):
    """
    Test the message size limit.
    """
    with source_app.test_client() as app:
        InstanceConfig.get_default().update_submission_prefs(
            allow_uploads=True, min_length=10, reject_codenames=False)
        new_codename(app, session)
        resp = app.post(
            url_for('main.submit'),
            data=dict(msg="A" * 5, fh=(StringIO(''), '')),
            follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Your first message must be at least 10 characters long." in text
        # Now retry with a longer message
        resp = app.post(
            url_for('main.submit'),
            data=dict(msg="A" * 25, fh=(StringIO(''), '')),
            follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Thank you for sending this information to us." in text
        # Now send another short message, that should still be accepted since
        # it's no longer the initial one
        resp = app.post(
            url_for('main.submit'),
            data=dict(msg="A", fh=(StringIO(''), '')),
            follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Thanks! We received your message." in text


def test_submit_file(source_app):
    with source_app.test_client() as app:
        new_codename(app, session)
        _dummy_submission(app)
        resp = app.post(
            url_for('main.submit'),
            data=dict(msg="", fh=(BytesIO(b'This is a test'), 'test.txt')),
            follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert 'Thanks! We received your document' in text


def test_submit_both(source_app):
    with source_app.test_client() as app:
        new_codename(app, session)
        _dummy_submission(app)
        resp = app.post(
            url_for('main.submit'),
            data=dict(
                msg="This is a test",
                fh=(BytesIO(b'This is a test'), 'test.txt')),
            follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Thanks! We received your message and document" in text


def test_submit_antispam(source_app):
    """
    Test the antispam check.
    """
    with source_app.test_client() as app:
        new_codename(app, session)
        _dummy_submission(app)
        resp = app.post(
            url_for('main.submit'),
            data=dict(msg="Test", fh=(StringIO(''), ''), text="blah"),
            follow_redirects=True)
        assert resp.status_code == 403


def test_submit_codename(source_app):
    """
    Test preventions against people submitting their codename.
    """
    with source_app.test_client() as app:
        InstanceConfig.get_default().update_submission_prefs(
            allow_uploads=True, min_length=0, reject_codenames=True)
        codename = new_codename(app, session)
        resp = app.post(
            url_for('main.submit'),
            data=dict(msg=codename, fh=(StringIO(''), '')),
            follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Please do not submit your codename!" in text
        # Do a dummy submission
        _dummy_submission(app)
        # Now resubmit the codename, should be accepted.
        resp = app.post(
            url_for('main.submit'),
            data=dict(msg=codename, fh=(StringIO(''), '')),
            follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Thanks! We received your message" in text


def test_delete_all_successfully_deletes_replies(source_app, app_storage):
    with source_app.app_context():
        journalist, _ = utils.db_helper.init_journalist()
        source, codename = utils.db_helper.init_source(app_storage)
        source_id = source.id
        utils.db_helper.reply(app_storage, journalist, source, 1)

    with source_app.test_client() as app:
        resp = app.post(url_for('main.login'),
                        data=dict(codename=codename),
                        follow_redirects=True)
        assert resp.status_code == 200
        resp = app.post(url_for('main.batch_delete'), follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "All replies have been deleted" in text

    with source_app.app_context():
        source = Source.query.get(source_id)
        replies = Reply.query.filter(Reply.source_id == source_id).all()
        for reply in replies:
            assert reply.deleted_by_source is True


def test_delete_all_replies_deleted_by_source_but_not_journalist(source_app, app_storage):
    """Replies can be deleted by a source, but not by journalists. As such,
    replies may still exist in the replies table, but no longer be visible."""
    with source_app.app_context():
        journalist, _ = utils.db_helper.init_journalist()
        source, codename = utils.db_helper.init_source(app_storage)
        utils.db_helper.reply(app_storage, journalist, source, 1)
        replies = Reply.query.filter(Reply.source_id == source.id).all()
        for reply in replies:
            reply.deleted_by_source = True
            db.session.add(reply)
            db.session.commit()

    with source_app.test_client() as app:
        with patch.object(source_app.logger, 'error') as logger:
            resp = app.post(url_for('main.login'),
                            data=dict(codename=codename),
                            follow_redirects=True)
            assert resp.status_code == 200
            resp = app.post(url_for('main.batch_delete'),
                            follow_redirects=True)
            assert resp.status_code == 200
            logger.assert_called_once_with(
                "Found no replies when at least one was expected"
            )


def test_delete_all_replies_already_deleted_by_journalists(source_app, app_storage):
    with source_app.app_context():
        journalist, _ = utils.db_helper.init_journalist()
        source, codename = utils.db_helper.init_source(app_storage)
        # Note that we are creating the source and no replies

    with source_app.test_client() as app:
        with patch.object(source_app.logger, 'error') as logger:
            resp = app.post(url_for('main.login'),
                            data=dict(codename=codename),
                            follow_redirects=True)
            assert resp.status_code == 200
            resp = app.post(url_for('main.batch_delete'),
                            follow_redirects=True)
            assert resp.status_code == 200
            logger.assert_called_once_with(
                "Found no replies when at least one was expected"
            )


def test_submit_sanitizes_filename(source_app):
    """Test that upload file name is sanitized"""
    insecure_filename = '../../bin/gpg'
    sanitized_filename = 'bin_gpg'

    with patch.object(gzip, 'GzipFile', wraps=gzip.GzipFile) as gzipfile:
        with source_app.test_client() as app:
            new_codename(app, session)
            resp = app.post(
                url_for('main.submit'),
                data=dict(
                    msg="",
                    fh=(BytesIO(b'This is a test'), insecure_filename)),
                follow_redirects=True)
            assert resp.status_code == 200
            gzipfile.assert_called_with(filename=sanitized_filename,
                                        mode=ANY,
                                        fileobj=ANY,
                                        mtime=0)


@pytest.mark.parametrize("test_url", ['main.index', 'main.create', 'main.submit'])
def test_redirect_when_tor2web(config, source_app, test_url):
    with source_app.test_client() as app:
        resp = app.get(
            url_for(test_url),
            headers=[('X-tor2web', 'encrypted')],
            follow_redirects=True)
        text = resp.data.decode('utf-8')
        assert resp.status_code == 403
        assert "Proxy Service Detected" in text

def test_tor2web_warning(source_app):
    with source_app.test_client() as app:
        resp = app.get(url_for('info.tor2web_warning'))
        assert resp.status_code == 403
        text = resp.data.decode('utf-8')
        assert "Proxy Service Detected" in text



def test_why_use_tor_browser(source_app):
    with source_app.test_client() as app:
        resp = app.get(url_for('info.recommend_tor_browser'))
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "You Should Use Tor Browser" in text


def test_why_journalist_key(source_app):
    with source_app.test_client() as app:
        resp = app.get(url_for('info.why_download_public_key'))
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Why download the team's public key?" in text


def test_metadata_route(config, source_app):
    with patch("server_os.get_os_release", return_value="20.04"):
        with source_app.test_client() as app:
            resp = app.get(url_for('api.metadata'))
            assert resp.status_code == 200
            assert resp.headers.get('Content-Type') == 'application/json'
            assert resp.json.get('allow_document_uploads') ==\
                InstanceConfig.get_current().allow_document_uploads
            assert resp.json.get('sd_version') == version.__version__
            assert resp.json.get('server_os') == '20.04'
            assert resp.json.get('supported_languages') ==\
                config.SUPPORTED_LOCALES
            assert resp.json.get('v3_source_url') is None


def test_metadata_v3_url(source_app):
    onion_test_url = "abcdefghabcdefghabcdefghabcdefghabcdefghabcdefghabcdefgh.onion"
    with patch.object(source_app_api, "get_sourcev3_url") as mocked_v3_url:
        mocked_v3_url.return_value = (onion_test_url)
        with source_app.test_client() as app:
            resp = app.get(url_for('api.metadata'))
            assert resp.status_code == 200
            assert resp.headers.get('Content-Type') == 'application/json'
            assert resp.json.get('v3_source_url') == onion_test_url


def test_login_with_overly_long_codename(source_app):
    """Attempting to login with an overly long codename should result in
    an error to avoid DoS."""
    overly_long_codename = 'a' * (PassphraseGenerator.MAX_PASSPHRASE_LENGTH + 1)
    with source_app.test_client() as app:
        resp = app.post(url_for('main.login'),
                        data=dict(codename=overly_long_codename),
                        follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert ("Field must be between 1 and {} characters long."
                .format(PassphraseGenerator.MAX_PASSPHRASE_LENGTH)) in text


def test_normalize_timestamps(source_app, app_storage):
    """
    Check function of source_app.utils.normalize_timestamps.

    All submissions for a source should have the same timestamp. Any
    existing submissions' files that did not exist at the time of a
    new submission should not be created by normalize_timestamps.
    """
    with source_app.test_client() as app:
        # create a source
        source, codename = utils.db_helper.init_source(app_storage)

        # create one submission
        first_submission = submit(app_storage, source, 1)[0]

        # delete the submission's file from the store
        first_submission_path = Path(
            app_storage.path(source.filesystem_id, first_submission.filename)
        )
        first_submission_path.unlink()
        assert not first_submission_path.exists()

        # log in as the source
        resp = app.post(url_for('main.login'),
                        data=dict(codename=codename),
                        follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Submit Files" in text
        assert SessionManager.is_user_logged_in(db_session=db.session)

        # submit another message
        resp = _dummy_submission(app)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Thanks! We received your message" in text

        # sleep to ensure timestamps would differ
        time.sleep(1)

        # submit another message
        resp = _dummy_submission(app)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Thanks! We received your message" in text

        # only two of the source's three submissions should have files in the store
        assert 3 == len(source.submissions)
        submission_paths = [
            Path(app_storage.path(source.filesystem_id, s.filename))
            for s in source.submissions
        ]
        extant_paths = [p for p in submission_paths if p.exists()]
        assert 2 == len(extant_paths)

        # verify that the deleted file has not been recreated
        assert not first_submission_path.exists()
        assert first_submission_path not in extant_paths

        # and the timestamps of all existing files should match exactly
        assert extant_paths[0].stat().st_atime_ns == extant_paths[1].stat().st_atime_ns
        assert extant_paths[0].stat().st_ctime_ns == extant_paths[1].stat().st_ctime_ns
        assert extant_paths[0].stat().st_mtime_ns == extant_paths[1].stat().st_mtime_ns


def test_failed_normalize_timestamps_logs_warning(source_app):
    """If a normalize timestamps event fails, the subprocess that calls
    touch will fail and exit 1. When this happens, the submission should
    still occur, but a warning should be logged (this will trigger an
    OSSEC alert)."""

    with patch.object(source_app.logger, 'warning') as logger:
        with patch.object(subprocess, 'call', return_value=1):
            with source_app.test_client() as app:
                new_codename(app, session)
                _dummy_submission(app)
                resp = app.post(
                    url_for('main.submit'),
                    data=dict(
                        msg="This is a test.",
                        fh=(StringIO(''), '')),
                    follow_redirects=True)
                assert resp.status_code == 200
                text = resp.data.decode('utf-8')
                assert "Thanks! We received your message" in text

                logger.assert_called_once_with(
                    "Couldn't normalize submission "
                    "timestamps (touch exited with 1)"
                )


def test_source_is_deleted_while_logged_in(source_app):
    """If a source is deleted by a journalist when they are logged in,
    a NoResultFound will occur. The source should be redirected to the
    index when this happens, and a warning logged."""
    with source_app.test_client() as app:
        codename = new_codename(app, session)
        app.post('login', data=dict(codename=codename), follow_redirects=True)

        # Now that the source is logged in, the journalist deletes the source
        source_user = SessionManager.get_logged_in_user(db_session=db.session)
        delete_collection(source_user.filesystem_id)

        # Source attempts to continue to navigate
        resp = app.get(url_for('main.lookup'), follow_redirects=True)
        assert resp.status_code == 200
        assert not SessionManager.is_user_logged_in(db_session=db.session)
        text = resp.data.decode('utf-8')
        assert 'First submission' in text
        assert not SessionManager.is_user_logged_in(db_session=db.session)


def test_login_with_invalid_codename(source_app):
    """Logging in with a codename with invalid characters should return
    an informative message to the user."""

    invalid_codename = '[]'

    with source_app.test_client() as app:
        resp = app.post(url_for('main.login'),
                        data=dict(codename=invalid_codename),
                        follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Invalid input." in text


def test_source_session_expiration(source_app):
    with source_app.test_client() as app:
        # Given a source user who logs in
        codename = new_codename(app, session)
        resp = app.post(url_for('main.login'),
                        data=dict(codename=codename),
                        follow_redirects=True)
        assert resp.status_code == 200

        # But we're now 6 hours later hence their session expired
        with mock.patch("source_app.session_manager.datetime") as mock_datetime:
            six_hours_later = datetime.now(timezone.utc) + timedelta(hours=6)
            mock_datetime.now.return_value = six_hours_later

            # When they browse to an authenticated page
            resp = app.get(url_for('main.lookup'), follow_redirects=True)

        # They get redirected to the index page with the "logged out" message
        text = resp.data.decode('utf-8')
        assert 'You were logged out due to inactivity' in text


def test_source_session_expiration_create(source_app):
    with source_app.test_client() as app:
        # Given a source user who is in the middle of the account creation flow
        resp = app.post(url_for('main.generate'), data=GENERATE_DATA)
        assert resp.status_code == 200

        # But we're now 6 hours later hence they did not finish the account creation flow in time
        with mock.patch("source_app.main.datetime") as mock_datetime:
            six_hours_later = datetime.now(timezone.utc) + timedelta(hours=6)
            mock_datetime.now.return_value = six_hours_later

            # When the user tries to complete the create flow
            resp = app.post(url_for('main.create'), follow_redirects=True)

        # They get redirected to the index page with the "logged out" message
        text = resp.data.decode('utf-8')
        assert 'You were logged out due to inactivity' in text


def test_source_no_session_expiration_message_when_not_logged_in(source_app):
    with source_app.test_client() as app:
        # Given an unauthenticated source user
        resp = app.get(url_for('main.index'))
        assert resp.status_code == 200

        # And their session expired
        with mock.patch("source_app.session_manager.datetime") as mock_datetime:
            six_hours_later = datetime.utcnow() + timedelta(hours=6)
            mock_datetime.now.return_value = six_hours_later

        # When they browse again the index page
        refreshed_resp = app.get(url_for('main.index'), follow_redirects=True)

        # The session expiration message is NOT displayed
        text = refreshed_resp.data.decode('utf-8')
        assert 'You were logged out due to inactivity' not in text


def test_csrf_error_page(source_app):
    source_app.config['WTF_CSRF_ENABLED'] = True
    with source_app.test_client() as app:
        with InstrumentedApp(source_app) as ins:
            resp = app.post(url_for('main.create'))
            ins.assert_redirects(resp, url_for('main.index'))

        resp = app.post(url_for('main.create'), follow_redirects=True)
        text = resp.data.decode('utf-8')
        assert 'You were logged out due to inactivity' in text


def test_source_can_only_delete_own_replies(source_app, app_storage):
    '''This test checks for a bug an authenticated source A could delete
       replies send to source B by "guessing" the filename.
    '''
    source0, codename0 = utils.db_helper.init_source(app_storage)
    source1, codename1 = utils.db_helper.init_source(app_storage)
    journalist, _ = utils.db_helper.init_journalist()
    replies = utils.db_helper.reply(app_storage, journalist, source0, 1)
    filename = replies[0].filename
    confirmation_msg = 'Reply deleted'

    with source_app.test_client() as app:
        resp = app.post(url_for('main.login'),
                        data={'codename': codename1},
                        follow_redirects=True)
        assert resp.status_code == 200
        assert SessionManager.get_logged_in_user(db_session=db.session).db_record_id == source1.id

        resp = app.post(url_for('main.delete'),
                        data={'reply_filename': filename},
                        follow_redirects=True)
        assert resp.status_code == 404
        assert confirmation_msg not in resp.data.decode('utf-8')

    reply = Reply.query.filter_by(filename=filename).one()
    assert not reply.deleted_by_source

    with source_app.test_client() as app:
        resp = app.post(url_for('main.login'),
                        data={'codename': codename0},
                        follow_redirects=True)
        assert resp.status_code == 200
        assert SessionManager.get_logged_in_user(db_session=db.session).db_record_id == source0.id

        resp = app.post(url_for('main.delete'),
                        data={'reply_filename': filename},
                        follow_redirects=True)
        assert resp.status_code == 200
        assert confirmation_msg in resp.data.decode('utf-8')

    reply = Reply.query.filter_by(filename=filename).one()
    assert reply.deleted_by_source


def test_robots_txt(source_app):
    """Test that robots.txt works"""
    with source_app.test_client() as app:
        # Not using url_for here because we care about the actual URL path
        resp = app.get('/robots.txt')
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert 'Disallow: /' in text
