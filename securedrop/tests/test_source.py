# -*- coding: utf-8 -*-
import gzip
import re
import subprocess
import time
import os
import shutil

from io import BytesIO, StringIO

from flask import g
from flask import session, escape, url_for, request
from mock import patch, ANY

from passphrases import PassphraseGenerator
from source_app.session_manager import SessionManager
from . import utils
import version

from db import db
from journalist_app.utils import delete_collection
from models import InstanceConfig, Source, Reply
from source_app import main as source_app_main
from source_app import api as source_app_api
from .utils.db_helper import new_codename
from .utils.instrument import InstrumentedApp


def test_logo_default_available(config, source_app):
    # if the custom image is available, this test will fail
    custom_image_location = os.path.join(
        config.SECUREDROP_ROOT, "static/i/custom_logo.png"
    )
    if os.path.exists(custom_image_location):
        os.remove(custom_image_location)

    with source_app.test_client() as app:
        response = app.get(url_for('main.select_logo'), follow_redirects=False)

        assert response.status_code == 302
        observed_headers = response.headers
        assert 'Location' in list(observed_headers.keys())
        assert url_for('static', filename='i/logo.png') in observed_headers['Location']


def test_logo_custom_available(config, source_app):
    # if the custom image is available, this test will fail
    custom_image = os.path.join(config.SECUREDROP_ROOT, "static/i/custom_logo.png")
    default_image = os.path.join(config.SECUREDROP_ROOT, "static/i/logo.png")
    if os.path.exists(default_image) and not os.path.exists(custom_image):
        shutil.copyfile(default_image, custom_image)

    with source_app.test_client() as app:
        response = app.get(url_for('main.select_logo'), follow_redirects=False)

        assert response.status_code == 302
        observed_headers = response.headers
        assert 'Location' in list(observed_headers.keys())
        assert url_for('static', filename='i/custom_logo.png') in observed_headers['Location']


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
    codename_re = (r'<p [^>]*id="codename"[^>]*>'
                   r'(?P<codename>[a-z0-9 &#;?:=@_.*+()\'"$%!-]+)</p>')
    codename_match = re.search(codename_re, html)
    assert codename_match is not None
    return codename_match.group('codename')


def test_generate_already_logged_in(source_app):
    with source_app.test_client() as app:
        new_codename(app, session)
        # Make sure it redirects to /lookup when logged in
        resp = app.get(url_for('main.generate'))
        assert resp.status_code == 302
        # Make sure it flashes the message on the lookup page
        resp = app.get(url_for('main.generate'), follow_redirects=True)
        # Should redirect to /lookup
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "because you are already logged in." in text


def test_create_new_source(source_app):
    with source_app.test_client() as app:
        resp = app.get(url_for('main.generate'))
        assert resp.status_code == 200
        tab_id = next(iter(session['codenames'].keys()))
        resp = app.post(url_for('main.create'), data={'tab_id': tab_id}, follow_redirects=True)
        assert SessionManager.is_user_logged_in()
        # should be redirected to /lookup
        text = resp.data.decode('utf-8')
        assert "Submit Files" in text
        assert 'codenames' not in session


def test_generate(source_app):
    with source_app.test_client() as app:
        resp = app.get(url_for('main.generate'))
        assert resp.status_code == 200
        session_codename = next(iter(session['codenames'].values()))

    text = resp.data.decode('utf-8')
    assert "This codename is what you will use in future visits" in text

    codename = _find_codename(resp.data.decode('utf-8'))
    # codename is also stored in the session - make sure it matches the
    # codename displayed to the source
    assert codename == escape(session_codename)


def test_create_duplicate_codename_logged_in_not_in_session(source_app):
    with source_app.test_client() as app:
        resp = app.get(url_for('main.generate'))
        assert resp.status_code == 200
        tab_id, codename = next(iter(session['codenames'].items()))

        # Create a source the first time
        resp = app.post(url_for('main.create'), data={'tab_id': tab_id}, follow_redirects=True)
        assert resp.status_code == 200
        codename = session['codename']

    with source_app.test_client() as app:
        # Attempt to add the same source
        with app.session_transaction() as sess:
            sess['codenames'] = {tab_id: codename}
        resp = app.post(url_for('main.create'), data={'tab_id': tab_id}, follow_redirects=True)
        assert resp.status_code == 200
        assert not SessionManager.is_user_logged_in()


def test_create_duplicate_codename_logged_in_in_session(source_app):
    with source_app.test_client() as app:
        resp = app.get(url_for('main.generate'))
        assert resp.status_code == 200
        tab_id = next(iter(session['codenames'].keys()))
        resp = app.post(url_for('main.create'), data={'tab_id': tab_id}, follow_redirects=True)
        assert resp.status_code == 200
        first_user = SessionManager.get_logged_in_user()
        with app.session_transaction() as sess:
            first_user_session_id = sess[SessionManager._KEY_FOR_SESSION_ID]

    # Attempt to add another source in the same session
    with source_app.test_client() as app:
        resp = app.get(url_for('main.generate'))
        assert resp.status_code == 200
        tab_id = next(iter(session['codenames'].keys()))

        with app.session_transaction() as sess:
            sess[SessionManager._KEY_FOR_SESSION_ID] = first_user_session_id

        resp = app.post(url_for('main.create'), data={'tab_id': tab_id}, follow_redirects=True)
        assert resp.status_code == 200
        final_user = SessionManager.get_logged_in_user()

        assert final_user.filesystem_id == first_user.filesystem_id
        text = resp.data.decode('utf-8')
        assert "You are already logged in." in text
        assert "Submit Files" in text


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
        assert SessionManager.is_user_logged_in()

    with source_app.test_client() as app:
        resp = app.post(url_for('main.login'),
                        data=dict(codename='invalid'),
                        follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert 'Sorry, that is not a recognized codename.' in text
        assert not SessionManager.is_user_logged_in()

    with source_app.test_client() as app:
        resp = app.post(url_for('main.login'),
                        data=dict(codename=codename),
                        follow_redirects=True)
        assert resp.status_code == 200
        assert SessionManager.is_user_logged_in()

        resp = app.post(url_for('main.login'),
                        data=dict(codename=codename),
                        follow_redirects=True)
        assert resp.status_code == 200
        assert SessionManager.is_user_logged_in()

        resp = app.get(url_for('main.logout'),
                       follow_redirects=True)
        assert 'logged_in' not in session
        assert 'codename' not in session
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
        assert SessionManager.is_user_logged_in()

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


def test_login_with_missing_reply_files(source_app):
    """
    Test that source can log in when replies are present in database but missing
    from storage.
    """
    source, codename = utils.db_helper.init_source()
    journalist, _ = utils.db_helper.init_journalist()
    replies = utils.db_helper.reply(journalist, source, 1)
    assert len(replies) > 0
    with source_app.test_client() as app:
        with patch("io.open") as ioMock:
            ioMock.side_effect = FileNotFoundError
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
            assert SessionManager.is_user_logged_in()


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


def test_submit_message_with_low_entropy(source_app):
    with patch.object(source_app_main, 'async_genkey') as async_genkey:
        with patch.object(source_app_main, 'get_entropy_estimate') \
                as get_entropy_estimate:
            get_entropy_estimate.return_value = 300

            with source_app.test_client() as app:
                new_codename(app, session)
                _dummy_submission(app)
                resp = app.post(
                    url_for('main.submit'),
                    data=dict(msg="This is a test.", fh=(StringIO(''), '')),
                    follow_redirects=True)
                assert resp.status_code == 200
                assert not async_genkey.called


def test_submit_message_with_enough_entropy(source_app):
    with patch.object(source_app_main, 'async_genkey') as async_genkey:
        with patch.object(source_app_main, 'get_entropy_estimate') \
                as get_entropy_estimate:
            get_entropy_estimate.return_value = 2400

            with source_app.test_client() as app:
                new_codename(app, session)
                _dummy_submission(app)
                resp = app.post(
                    url_for('main.submit'),
                    data=dict(msg="This is a test.", fh=(StringIO(''), '')),
                    follow_redirects=True)
                assert resp.status_code == 200
                assert async_genkey.called


def test_delete_all_successfully_deletes_replies(source_app):
    with source_app.app_context():
        journalist, _ = utils.db_helper.init_journalist()
        source, codename = utils.db_helper.init_source()
        source_id = source.id
        utils.db_helper.reply(journalist, source, 1)

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


def test_delete_all_replies_deleted_by_source_but_not_journalist(source_app):
    """Replies can be deleted by a source, but not by journalists. As such,
    replies may still exist in the replies table, but no longer be visible."""
    with source_app.app_context():
        journalist, _ = utils.db_helper.init_journalist()
        source, codename = utils.db_helper.init_source()
        utils.db_helper.reply(journalist, source, 1)
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


def test_delete_all_replies_already_deleted_by_journalists(source_app):
    with source_app.app_context():
        journalist, _ = utils.db_helper.init_journalist()
        source, codename = utils.db_helper.init_source()
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


def test_tor2web_warning_headers(source_app):
    with source_app.test_client() as app:
        resp = app.get(url_for('main.index'),
                       headers=[('X-tor2web', 'encrypted')])
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "You appear to be using Tor2Web." in text


def test_tor2web_warning(source_app):
    with source_app.test_client() as app:
        resp = app.get(url_for('info.tor2web_warning'))
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Why is there a warning about Tor2Web?" in text


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
    with patch.object(source_app_api, "server_os", new="16.04"):
        with source_app.test_client() as app:
            resp = app.get(url_for('api.metadata'))
            assert resp.status_code == 200
            assert resp.headers.get('Content-Type') == 'application/json'
            assert resp.json.get('allow_document_uploads') ==\
                InstanceConfig.get_current().allow_document_uploads
            assert resp.json.get('sd_version') == version.__version__
            assert resp.json.get('server_os') == '16.04'
            assert resp.json.get('supported_languages') ==\
                config.SUPPORTED_LOCALES
            assert resp.json.get('v2_source_url') is None
            assert resp.json.get('v3_source_url') is None


def test_metadata_v2_url(source_app):
    onion_test_url = "abcdabcdabcdabcd.onion"
    with patch.object(source_app_api, "get_sourcev2_url") as mocked_v2_url:
        mocked_v2_url.return_value = (onion_test_url)
        with source_app.test_client() as app:
            resp = app.get(url_for('api.metadata'))
            assert resp.status_code == 200
            assert resp.headers.get('Content-Type') == 'application/json'
            assert resp.json.get('v2_source_url') == onion_test_url
            assert resp.json.get('v3_source_url') is None


def test_metadata_v3_url(source_app):
    onion_test_url = "abcdefghabcdefghabcdefghabcdefghabcdefghabcdefghabcdefgh.onion"
    with patch.object(source_app_api, "get_sourcev3_url") as mocked_v3_url:
        mocked_v3_url.return_value = (onion_test_url)
        with source_app.test_client() as app:
            resp = app.get(url_for('api.metadata'))
            assert resp.status_code == 200
            assert resp.headers.get('Content-Type') == 'application/json'
            assert resp.json.get('v2_source_url') is None
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


def test_failed_normalize_timestamps_logs_warning(source_app):
    """If a normalize timestamps event fails, the subprocess that calls
    touch will fail and exit 1. When this happens, the submission should
    still occur, but a warning should be logged (this will trigger an
    OSSEC alert)."""

    with patch("source_app.main.get_entropy_estimate", return_value=8192):
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
        source_user = SessionManager.get_logged_in_user()
        delete_collection(source_user.filesystem_id)

        # Source attempts to continue to navigate
        resp = app.get(url_for('main.lookup'), follow_redirects=True)
        assert resp.status_code == 200
        assert not SessionManager.is_user_logged_in()
        text = resp.data.decode('utf-8')
        assert 'First submission' in text
        assert not SessionManager.is_user_logged_in()


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


def test_source_session_expiration(config, source_app):
    with source_app.test_client() as app:
        # Given a source user who logs in
        codename = new_codename(app, session)
        resp = app.post(url_for('main.login'),
                        data=dict(codename=codename),
                        follow_redirects=True)
        assert resp.status_code == 200

        # And their session expired just now
        SessionManager.log_all_users_out()

        # When they browse to an authenticated page
        resp = app.get(url_for('main.lookup'), follow_redirects=True)

        # They get redirected to the index page with the "logged out" message
        text = resp.data.decode('utf-8')
        assert 'You were logged out due to inactivity' in text


def test_source_session_expiration_create(config, source_app):
    with source_app.test_client() as app:
        seconds_session_expire = 1
        config.SESSION_EXPIRATION_MINUTES = seconds_session_expire / 60.

        # Given a source user who is in the middle of the account creation flow
        resp = app.get(url_for('main.generate'))
        assert resp.status_code == 200

        # And they don't finish the account creation flow in time
        time.sleep(seconds_session_expire + 0.1)

        # When the user tries to complete the create flow
        resp = app.post(url_for('main.create'), follow_redirects=True)

        # They get redirected to the index page with the "logged out" message
        text = resp.data.decode('utf-8')
        assert 'You were logged out due to inactivity' in text


def test_source_no_session_expiration_message_when_not_logged_in(config, source_app):
    with source_app.test_client() as app:
        seconds_session_expire = 1
        config.SESSION_EXPIRATION_MINUTES = seconds_session_expire / 60.

        # Given an unauthenticated source user
        resp = app.get(url_for('main.index'))
        assert resp.status_code == 200

        # And their session cookie expired just now
        time.sleep(seconds_session_expire + 1)

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


def test_source_can_only_delete_own_replies(source_app):
    '''This test checks for a bug an authenticated source A could delete
       replies send to source B by "guessing" the filename.
    '''
    source0, codename0 = utils.db_helper.init_source()
    source1, codename1 = utils.db_helper.init_source()
    journalist, _ = utils.db_helper.init_journalist()
    replies = utils.db_helper.reply(journalist, source0, 1)
    filename = replies[0].filename
    confirmation_msg = 'Reply deleted'

    with source_app.test_client() as app:
        resp = app.post(url_for('main.login'),
                        data={'codename': codename1},
                        follow_redirects=True)
        assert resp.status_code == 200
        assert SessionManager.get_logged_in_user().db_record_id == source1.id

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
        assert SessionManager.get_logged_in_user().db_record_id == source0.id

        resp = app.post(url_for('main.delete'),
                        data={'reply_filename': filename},
                        follow_redirects=True)
        assert resp.status_code == 200
        assert confirmation_msg in resp.data.decode('utf-8')

    reply = Reply.query.filter_by(filename=filename).one()
    assert reply.deleted_by_source
