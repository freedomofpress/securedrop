# -*- coding: utf-8 -*-
import gzip
import re
import subprocess
import time

from io import BytesIO, StringIO
from flask import session, escape, current_app, url_for, g
from mock import patch, ANY

import crypto_util
import source
from . import utils
import version

from db import db
from models import InstanceConfig, Source, Reply
from source_app import main as source_app_main
from source_app import api as source_app_api
from .utils.db_helper import new_codename
from .utils.instrument import InstrumentedApp

overly_long_codename = 'a' * (Source.MAX_CODENAME_LEN + 1)


def test_page_not_found(source_app):
    """Verify the page not found condition returns the intended template"""
    with InstrumentedApp(source_app) as ins:
        with source_app.test_client() as app:
            resp = app.get('UNKNOWN')
            assert resp.status_code == 404
            ins.assert_template_used('notfound.html')


def test_index(source_app):
    """Test that the landing page loads and looks how we expect"""
    with source_app.test_client() as app:
        resp = app.get(url_for('main.index'))
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert 'First submission' in text
        assert 'Return visit' in text


def test_all_words_in_wordlist_validate(source_app):
    """Verify that all words in the wordlist are allowed by the form
    validation. Otherwise a source will have a codename and be unable to
    return."""

    with source_app.app_context():
        wordlist_en = current_app.crypto_util.get_wordlist('en')

    # chunk the words to cut down on the number of requets we make
    # otherwise this test is *slow*
    chunks = [wordlist_en[i:i + 7] for i in range(0, len(wordlist_en), 7)]

    with source_app.test_client() as app:
        for words in chunks:
            resp = app.post(url_for('main.login'),
                            data=dict(codename=' '.join(words)),
                            follow_redirects=True)
            assert resp.status_code == 200
            text = resp.data.decode('utf-8')
            # If the word does not validate, then it will show
            # 'Invalid input'. If it does validate, it should show that
            # it isn't a recognized codename.
            assert 'Sorry, that is not a recognized codename.' in text
            assert 'logged_in' not in session


def _find_codename(html):
    """Find a source codename (diceware passphrase) in HTML"""
    # Codenames may contain HTML escape characters, and the wordlist
    # contains various symbols.
    codename_re = (r'<p [^>]*id="codename"[^>]*>'
                   r'(?P<codename>[a-z0-9 &#;?:=@_.*+()\'"$%!-]+)</p>')
    codename_match = re.search(codename_re, html)
    assert codename_match is not None
    return codename_match.group('codename')


def test_generate(source_app):
    with source_app.test_client() as app:
        resp = app.get(url_for('main.generate'))
        assert resp.status_code == 200
        session_codename = session['codename']

    text = resp.data.decode('utf-8')
    assert "This codename is what you will use in future visits" in text

    codename = _find_codename(resp.data.decode('utf-8'))
    assert len(codename.split()) == Source.NUM_WORDS
    # codename is also stored in the session - make sure it matches the
    # codename displayed to the source
    assert codename == escape(session_codename)


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
        resp = app.post(url_for('main.create'), follow_redirects=True)
        assert session['logged_in'] is True
        # should be redirected to /lookup
        text = resp.data.decode('utf-8')
        assert "Submit Files" in text


def test_generate_too_long_codename(source_app):
    """Generate a codename that exceeds the maximum codename length"""

    with patch.object(source_app.logger, 'warning') as logger:
        with patch.object(crypto_util.CryptoUtil, 'genrandomid',
                          side_effect=[overly_long_codename,
                                       'short codename']):
            with source_app.test_client() as app:
                resp = app.post(url_for('main.generate'))
                assert resp.status_code == 200

    logger.assert_called_with(
        "Generated a source codename that was too long, "
        "skipping it. This should not happen. "
        "(Codename='{}')".format(overly_long_codename)
    )


def test_create_duplicate_codename_logged_in_not_in_session(source_app):
    with patch.object(source.app.logger, 'error') as logger:
        with source_app.test_client() as app:
            resp = app.get(url_for('main.generate'))
            assert resp.status_code == 200

            # Create a source the first time
            resp = app.post(url_for('main.create'), follow_redirects=True)
            assert resp.status_code == 200
            codename = session['codename']

        with source_app.test_client() as app:
            # Attempt to add the same source
            with app.session_transaction() as sess:
                sess['codename'] = codename
            resp = app.post(url_for('main.create'), follow_redirects=True)
            logger.assert_called_once()
            assert ("Attempt to create a source with duplicate codename"
                    in logger.call_args[0][0])
            assert resp.status_code == 500
            assert 'codename' not in session
            assert 'logged_in' not in session


def test_create_duplicate_codename_logged_in_in_session(source_app):
    with patch.object(source.app.logger, 'error') as logger:
        with source_app.test_client() as app:
            resp = app.get(url_for('main.generate'))
            assert resp.status_code == 200

            # Create a source the first time
            resp = app.post(url_for('main.create'), follow_redirects=True)
            assert resp.status_code == 200

            # Attempt to add the same source
            resp = app.post(url_for('main.create'), follow_redirects=True)
            logger.assert_called_once()
            assert ("Attempt to create a source with duplicate codename"
                    in logger.call_args[0][0])
            assert resp.status_code == 500
            assert 'codename' not in session

            # Reproducer for bug #4361
            resp = app.post(url_for('main.index'), follow_redirects=True)
            assert 'logged_in' not in session


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
        resp = app.get(url_for('info.download_journalist_pubkey'))
        text = resp.data.decode('utf-8')
        assert "BEGIN PGP PUBLIC KEY BLOCK" in text


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
        assert session['logged_in'] is True

    with source_app.test_client() as app:
        resp = app.post(url_for('main.login'),
                        data=dict(codename='invalid'),
                        follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert 'Sorry, that is not a recognized codename.' in text
        assert 'logged_in' not in session

    with source_app.test_client() as app:
        resp = app.post(url_for('main.login'),
                        data=dict(codename=codename),
                        follow_redirects=True)
        assert resp.status_code == 200
        assert session['logged_in'] is True

        resp = app.post(url_for('main.login'),
                        data=dict(codename=codename),
                        follow_redirects=True)
        assert resp.status_code == 200
        assert session['logged_in'] is True

        resp = app.get(url_for('main.logout'),
                       follow_redirects=True)
        assert 'logged_in' not in session
        assert 'codename' not in session
        text = resp.data.decode('utf-8')
        assert 'Thank you for exiting your session!' in text


def test_user_must_log_in_for_protected_views(source_app):
    with source_app.test_client() as app:
        resp = app.get(url_for('main.lookup'),
                       follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Enter Codename" in text


def test_login_with_whitespace(source_app):
    """
    Test that codenames with leading or trailing whitespace still work"""

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
        assert session['logged_in'] is True

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
    '''
    When the message is larger than 512KB it's written to disk instead of
    just residing in memory. Make sure the different return type of
    SecureTemporaryFile is handled as well as BytesIO.
    '''
    with source_app.test_client() as app:
        new_codename(app, session)
        _dummy_submission(app)
        resp = app.post(
            url_for('main.submit'),
            data=dict(msg="AA" * (1024 * 512), fh=(StringIO(''), '')),
            follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Thanks! We received your message" in text


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
        resp = app.get(url_for('info.why_download_journalist_pubkey'))
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Why download the journalist's public key?" in text


def test_metadata_route(config, source_app):
    with patch.object(source_app_api.platform, "linux_distribution") as mocked_platform:
        mocked_platform.return_value = ("Ubuntu", "16.04", "xenial")
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


def test_login_with_overly_long_codename(source_app):
    """Attempting to login with an overly long codename should result in
    an error, and scrypt should not be called to avoid DoS."""
    with patch.object(crypto_util.CryptoUtil, 'hash_codename') \
            as mock_hash_codename:
        with source_app.test_client() as app:
            resp = app.post(url_for('main.login'),
                            data=dict(codename=overly_long_codename),
                            follow_redirects=True)
            assert resp.status_code == 200
            text = resp.data.decode('utf-8')
            assert ("Field must be between 1 and {} characters long."
                    .format(Source.MAX_CODENAME_LEN)) in text
            assert not mock_hash_codename.called, \
                "Called hash_codename for codename w/ invalid length"


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

    with patch.object(source_app.logger, 'error') as logger:
        with source_app.test_client() as app:
            codename = new_codename(app, session)
            resp = app.post('login', data=dict(codename=codename),
                            follow_redirects=True)

            # Now the journalist deletes the source
            filesystem_id = source_app.crypto_util.hash_codename(codename)
            source_app.crypto_util.delete_reply_keypair(filesystem_id)
            source = Source.query.filter_by(
                filesystem_id=filesystem_id).one()
            db.session.delete(source)
            db.session.commit()

            # Source attempts to continue to navigate
            resp = app.post(url_for('main.lookup'), follow_redirects=True)
            assert resp.status_code == 200
            text = resp.data.decode('utf-8')
            assert 'First submission' in text
            assert 'logged_in' not in session
            assert 'codename' not in session

        logger.assert_called_once_with(
            "Found no Sources when one was expected: "
            "No row was found for one()")


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
        codename = new_codename(app, session)

        # set the expiration to ensure we trigger an expiration
        config.SESSION_EXPIRATION_MINUTES = -1

        resp = app.post(url_for('main.login'),
                        data=dict(codename=codename),
                        follow_redirects=True)
        assert resp.status_code == 200
        resp = app.get(url_for('main.lookup'), follow_redirects=True)

        # check that the session was cleared (apart from 'expires'
        # which is always present and 'csrf_token' which leaks no info)
        session.pop('expires', None)
        session.pop('csrf_token', None)
        assert not session

        text = resp.data.decode('utf-8')
        assert 'Your session timed out due to inactivity' in text


def test_source_session_expiration_create(config, source_app):
    with source_app.test_client() as app:

        seconds_session_expire = 1
        config.SESSION_EXPIRATION_MINUTES = seconds_session_expire / 60.

        # Make codename, and then wait for session to expire.
        resp = app.get(url_for('main.generate'))
        assert resp.status_code == 200

        time.sleep(seconds_session_expire + 0.1)

        # Now when we click create, the session will have expired.
        resp = app.post(url_for('main.create'), follow_redirects=True)

        # check that the session was cleared (apart from 'expires'
        # which is always present and 'csrf_token' which leaks no info)
        session.pop('expires', None)
        session.pop('csrf_token', None)
        assert not session

        text = resp.data.decode('utf-8')
        assert 'Your session timed out due to inactivity' in text


def test_csrf_error_page(config, source_app):
    source_app.config['WTF_CSRF_ENABLED'] = True
    with source_app.test_client() as app:
        with InstrumentedApp(source_app) as ins:
            resp = app.post(url_for('main.create'))
            ins.assert_redirects(resp, url_for('main.index'))

        resp = app.post(url_for('main.create'), follow_redirects=True)
        text = resp.data.decode('utf-8')
        assert 'Your session timed out due to inactivity' in text


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
        assert g.source.id == source1.id

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
        assert g.source.id == source0.id

        resp = app.post(url_for('main.delete'),
                        data={'reply_filename': filename},
                        follow_redirects=True)
        assert resp.status_code == 200
        assert confirmation_msg in resp.data.decode('utf-8')

    reply = Reply.query.filter_by(filename=filename).one()
    assert reply.deleted_by_source
