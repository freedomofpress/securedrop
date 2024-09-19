import gzip
import os
import random
import re
import zipfile
from io import BytesIO
from unittest import mock

import journalist_app as journalist_app_module
from bs4 import BeautifulSoup
from db import db
from encryption import EncryptionManager
from flask import escape
from journalist_app.sessions import session
from source_app.session_manager import SessionManager
from store import Storage
from tests import utils
from tests.utils import login_journalist
from two_factor import TOTP

# Seed the RNG for deterministic testing
random.seed("ಠ_ಠ")
GENERATE_DATA = {"tor2web_check": 'href="fake.onion"'}


def test_submit_message(journalist_app, source_app, test_journo, app_storage):
    """When a source creates an account, test that a new entry appears
    in the journalist interface"""
    test_msg = "This is a test message."

    with source_app.test_client() as app:
        app.post("/generate", data=GENERATE_DATA)
        tab_id = next(iter(session["codenames"].keys()))
        app.post("/create", data={"tab_id": tab_id}, follow_redirects=True)
        source_user = SessionManager.get_logged_in_user(db_session=db.session)
        filesystem_id = source_user.filesystem_id

        # redirected to submission form
        resp = app.post(
            "/submit",
            data=dict(
                msg=test_msg,
                fh=(BytesIO(b""), ""),
            ),
            follow_redirects=True,
        )
        assert resp.status_code == 200
        resp = app.post("/logout")
        assert resp.status_code == 200

    # Request the Journalist Interface index
    with journalist_app.test_client() as app:
        login_journalist(
            app, test_journo["username"], test_journo["password"], test_journo["otp_secret"]
        )
        resp = app.get("/")
        assert resp.status_code == 200
        text = resp.data.decode("utf-8")
        assert "Sources" in text
        soup = BeautifulSoup(text, "html.parser")

        # The source should have a "download unread" link that
        # says "1 unread"
        col = soup.select("table#collections tr.source")[0]
        unread_span = col.select("td.unread a")[0]
        assert "1 unread" in unread_span.get_text()

        col_url = soup.select("table#collections th.designation a")[0]["href"]
        resp = app.get(col_url)
        assert resp.status_code == 200
        text = resp.data.decode("utf-8")
        soup = BeautifulSoup(text, "html.parser")
        submission_url = soup.select("table#submissions th.filename a")[0]["href"]
        assert "-msg" in submission_url
        size = soup.select("table#submissions td.info")[0]
        assert re.compile(r"\d+ bytes").match(size["title"])

        resp = app.get(submission_url)
        assert resp.status_code == 200

        decryption_result = utils.decrypt_as_journalist(resp.data).decode()
        assert decryption_result == test_msg

        # delete submission
        resp = app.get(col_url)
        assert resp.status_code == 200
        text = resp.data.decode("utf-8")
        soup = BeautifulSoup(text, "html.parser")
        doc_name = soup.select(
            'table#submissions > tr.submission > td.status input[name="doc_names_selected"]'
        )[0]["value"]
        resp = app.post(
            "/bulk",
            data=dict(
                action="delete",
                filesystem_id=filesystem_id,
                doc_names_selected=doc_name,
            ),
            follow_redirects=True,
        )
        assert resp.status_code == 200
        text = resp.data.decode("utf-8")
        soup = BeautifulSoup(text, "html.parser")
        assert "The item has been deleted." in text

        # confirm that submission deleted and absent in list of submissions
        resp = app.get(col_url)
        assert resp.status_code == 200
        text = resp.data.decode("utf-8")
        assert "No submissions to display." in text

        # the file should be deleted from the filesystem
        # since file deletion is handled by a polling worker, this test
        # needs to wait for the worker to get the job and execute it
        def assertion():
            assert not (os.path.exists(app_storage.path(filesystem_id, doc_name)))

        utils.asynchronous.wait_for_assertion(assertion)


def test_submit_file(journalist_app, source_app, test_journo, app_storage):
    """When a source creates an account, test that a new entry appears
    in the journalist interface"""
    test_file_contents = b"This is a test file."
    test_filename = "test.txt"

    with source_app.test_client() as app:
        app.post("/generate", data=GENERATE_DATA)
        tab_id = next(iter(session["codenames"].keys()))
        app.post("/create", data={"tab_id": tab_id}, follow_redirects=True)
        source_user = SessionManager.get_logged_in_user(db_session=db.session)
        filesystem_id = source_user.filesystem_id

        # redirected to submission form
        resp = app.post(
            "/submit",
            data=dict(
                msg="",
                fh=(BytesIO(test_file_contents), test_filename),
            ),
            follow_redirects=True,
        )
        assert resp.status_code == 200
        resp = app.post("/logout")
        assert resp.status_code == 200

    with journalist_app.test_client() as app:
        login_journalist(
            app, test_journo["username"], test_journo["password"], test_journo["otp_secret"]
        )
        resp = app.get("/")
        assert resp.status_code == 200
        text = resp.data.decode("utf-8")
        assert "Sources" in text
        soup = BeautifulSoup(text, "html.parser")

        # The source should have a "download unread" link that says
        # "1 unread"
        col = soup.select("table#collections tr.source")[0]
        unread_span = col.select("td.unread a")[0]
        assert "1 unread" in unread_span.get_text()

        col_url = soup.select("table#collections th.designation a")[0]["href"]
        resp = app.get(col_url)
        assert resp.status_code == 200
        text = resp.data.decode("utf-8")
        soup = BeautifulSoup(text, "html.parser")
        submission_url = soup.select("table#submissions th.filename a")[0]["href"]
        assert "-doc" in submission_url
        size = soup.select("table#submissions td.info")[0]
        assert re.compile(r"\d+ bytes").match(size["title"])

        resp = app.get(submission_url)
        assert resp.status_code == 200

        decrypted_data = utils.decrypt_as_journalist(resp.data)
        sio = BytesIO(decrypted_data)
        with gzip.GzipFile(mode="rb", fileobj=sio) as gzip_file:
            unzipped_decrypted_data = gzip_file.read()
            mtime = gzip_file.mtime
        assert unzipped_decrypted_data == test_file_contents
        # Verify gzip file metadata and ensure timestamp is not present.
        assert mtime == 0

        # delete submission
        resp = app.get(col_url)
        assert resp.status_code == 200
        text = resp.data.decode("utf-8")
        soup = BeautifulSoup(text, "html.parser")
        doc_name = soup.select(
            'table#submissions > tr.submission > td.status input[name="doc_names_selected"]'
        )[0]["value"]
        resp = app.post(
            "/bulk",
            data=dict(
                action="delete",
                filesystem_id=filesystem_id,
                doc_names_selected=doc_name,
            ),
            follow_redirects=True,
        )
        assert resp.status_code == 200
        text = resp.data.decode("utf-8")
        assert "The item has been deleted." in text
        soup = BeautifulSoup(resp.data, "html.parser")

        # confirm that submission deleted and absent in list of submissions
        resp = app.get(col_url)
        assert resp.status_code == 200
        text = resp.data.decode("utf-8")
        assert "No submissions to display." in text

        # the file should be deleted from the filesystem
        # since file deletion is handled by a polling worker, this test
        # needs to wait for the worker to get the job and execute it
        def assertion():
            assert not (os.path.exists(app_storage.path(filesystem_id, doc_name)))

        utils.asynchronous.wait_for_assertion(assertion)


def _helper_test_reply(journalist_app, source_app, test_journo, test_reply):
    test_msg = "This is a test message."

    with source_app.test_client() as app:
        app.post("/generate", data=GENERATE_DATA)
        tab_id, codename = next(iter(session["codenames"].items()))
        app.post("/create", data={"tab_id": tab_id}, follow_redirects=True)
        # redirected to submission form
        resp = app.post(
            "/submit",
            data=dict(
                msg=test_msg,
                fh=(BytesIO(b""), ""),
            ),
            follow_redirects=True,
        )
        assert resp.status_code == 200
        source_user = SessionManager.get_logged_in_user(db_session=db.session)
        filesystem_id = source_user.filesystem_id
        resp = app.post("/logout")
        assert resp.status_code == 200

    with journalist_app.test_client() as app:
        login_journalist(
            app, test_journo["username"], test_journo["password"], test_journo["otp_secret"]
        )
        resp = app.get("/")
        assert resp.status_code == 200
        text = resp.data.decode("utf-8")
        assert "Sources" in text
        soup = BeautifulSoup(resp.data, "html.parser")
        col_url = soup.select("table#collections tr.source > th.designation a")[0]["href"]

        resp = app.get(col_url)
        assert resp.status_code == 200

    # Create 2 replies to test deleting on journalist and source interface
    with journalist_app.test_client() as app:
        login_journalist(
            app, test_journo["username"], test_journo["password"], test_journo["otp_secret"]
        )
        for i in range(2):
            resp = app.post(
                "/reply",
                data=dict(filesystem_id=filesystem_id, message=test_reply),
                follow_redirects=True,
            )
            assert resp.status_code == 200

        text = resp.data.decode("utf-8")
        assert "The source will receive your reply" in text

        resp = app.get(col_url)
        text = resp.data.decode("utf-8")
        assert "reply-" in text

    soup = BeautifulSoup(text, "html.parser")

    # Download the reply and verify that it can be decrypted with the
    # journalist's key as well as the source's reply key
    filesystem_id = soup.select('input[name="filesystem_id"]')[0]["value"]
    checkbox_values = [soup.select('input[name="doc_names_selected"]')[1]["value"]]
    resp = app.post(
        "/bulk",
        data=dict(
            filesystem_id=filesystem_id,
            action="download",
            doc_names_selected=checkbox_values,
        ),
        follow_redirects=True,
    )
    assert resp.status_code == 200

    zf = zipfile.ZipFile(BytesIO(resp.data), "r")
    data = zf.read(zf.namelist()[0])
    journalist_decrypted = utils.decrypt_as_journalist(data).decode()
    assert journalist_decrypted == test_reply
    source_decrypted = EncryptionManager.get_default().decrypt_journalist_reply(source_user, data)
    assert source_decrypted == test_reply

    # Test deleting reply on the journalist interface
    last_reply_number = len(soup.select('input[name="doc_names_selected"]')) - 1
    _helper_filenames_delete(app, soup, last_reply_number)

    with source_app.test_client() as app:
        resp = app.post("/login", data=dict(codename=codename), follow_redirects=True)
        assert resp.status_code == 200
        resp = app.get("/lookup")
        assert resp.status_code == 200
        text = resp.data.decode("utf-8")

        assert "You have received a reply. To protect your identity" in text
        assert test_reply in text, text
        soup = BeautifulSoup(text, "html.parser")
        msgid = soup.select('form > input[name="reply_filename"]')[0]["value"]
        resp = app.post(
            "/delete",
            data=dict(filesystem_id=filesystem_id, reply_filename=msgid),
            follow_redirects=True,
        )
        assert resp.status_code == 200
        text = resp.data.decode("utf-8")
        assert "Reply deleted" in text

        resp = app.post("/logout")
        assert resp.status_code == 200


def _helper_filenames_delete(journalist_app, soup, i):
    filesystem_id = soup.select('input[name="filesystem_id"]')[0]["value"]
    checkbox_values = [soup.select('input[name="doc_names_selected"]')[i]["value"]]

    # delete
    resp = journalist_app.post(
        "/bulk",
        data=dict(
            filesystem_id=filesystem_id,
            action="delete",
            doc_names_selected=checkbox_values,
        ),
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "The item has been deleted." in resp.data.decode("utf-8")

    # Make sure the files were deleted from the filesystem
    def assertion():
        assert not any(
            [
                os.path.exists(Storage.get_default().path(filesystem_id, doc_name))
                for doc_name in checkbox_values
            ]
        )

    utils.asynchronous.wait_for_assertion(assertion)


def test_reply_normal(journalist_app, source_app, test_journo):
    """Test for regression on #1360 (failure to encode bytes before calling
    gpg functions).
    """
    encryption_mgr = EncryptionManager.get_default()
    encryption_mgr.gpg()  # lazily initialize GPG
    with mock.patch.object(encryption_mgr._gpg, "_encoding", "ansi_x3.4_1968"):
        _helper_test_reply(
            journalist_app,
            source_app,
            test_journo,
            "This is a test reply.",
        )


def test_unicode_reply_with_ansi_env(journalist_app, source_app, test_journo):
    # This makes python-gnupg handle encoding equivalent to if we were
    # running SD in an environment where os.getenv("LANG") == "C".
    # Unfortunately, with the way our test suite is set up simply setting
    # that env var here will not have the desired effect. Instead we
    # monkey-patch the GPG object that is called crypto_util to imitate the
    # _encoding attribute it would have had it been initialized in a "C"
    # environment. See
    # https://github.com/freedomofpress/securedrop/issues/1360 for context.
    encryption_mgr = EncryptionManager.get_default()
    encryption_mgr.gpg()  # lazily initialize GPG
    with mock.patch.object(encryption_mgr._gpg, "_encoding", "ansi_x3.4_1968"):
        _helper_test_reply(
            journalist_app,
            source_app,
            test_journo,
            "ᚠᛇᚻ᛫ᛒᛦᚦ᛫ᚠᚱᚩᚠᚢᚱ᛫ᚠᛁᚱᚪ᛫ᚷᛖᚻᚹᛦᛚᚳᚢᛗ",
        )


def test_delete_collection(mocker, source_app, journalist_app, test_journo):
    """Test the "delete collection" button on each collection page"""

    # first, add a source
    with source_app.test_client() as app:
        app.post("/generate", data=GENERATE_DATA)
        tab_id = next(iter(session["codenames"].keys()))
        app.post("/create", data={"tab_id": tab_id})
        resp = app.post(
            "/submit",
            data=dict(
                msg="This is a test.",
                fh=(BytesIO(b""), ""),
            ),
            follow_redirects=True,
        )
        assert resp.status_code == 200

    with journalist_app.test_client() as app:
        login_journalist(
            app, test_journo["username"], test_journo["password"], test_journo["otp_secret"]
        )
        resp = app.get("/")
        # navigate to the collection page
        soup = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
        first_col_url = soup.select("table#collections tr.source > th.designation a")[0]["href"]
        resp = app.get(first_col_url)
        assert resp.status_code == 200

        # find the delete form and extract the post parameters
        soup = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
        delete_form_inputs = soup.select("form#delete-collection")[0]("input")
        filesystem_id = delete_form_inputs[1]["value"]
        col_name = delete_form_inputs[2]["value"]

        resp = app.post("/col/delete/" + filesystem_id, follow_redirects=True)
        assert resp.status_code == 200

        text = resp.data.decode("utf-8")
        assert escape(f"The account and data for the source {col_name} have been deleted.") in text

        assert "There are no submissions!" in text

        # Make sure the collection is deleted from the filesystem
        def assertion():
            assert not os.path.exists(Storage.get_default().path(filesystem_id))

        utils.asynchronous.wait_for_assertion(assertion)


def test_delete_collections(mocker, journalist_app, source_app, test_journo):
    """Test the "delete selected" checkboxes on the index page that can be
    used to delete multiple collections"""

    # first, add some sources
    with source_app.test_client() as app:
        num_sources = 2
        for i in range(num_sources):
            app.post("/generate", data=GENERATE_DATA)
            tab_id = next(iter(session["codenames"].keys()))
            app.post("/create", data={"tab_id": tab_id})
            app.post(
                "/submit",
                data=dict(
                    msg="This is a test " + str(i) + ".",
                    fh=(BytesIO(b""), ""),
                ),
                follow_redirects=True,
            )
            resp = app.post("/logout")
            assert resp.status_code == 200

    with journalist_app.test_client() as app:
        login_journalist(
            app, test_journo["username"], test_journo["password"], test_journo["otp_secret"]
        )
        resp = app.get("/")
        # get all the checkbox values
        soup = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
        checkbox_values = [
            checkbox["value"] for checkbox in soup.select('input[name="cols_selected"]')
        ]

        resp = app.post(
            "/col/process",
            data=dict(action="delete", cols_selected=checkbox_values),
            follow_redirects=True,
        )
        assert resp.status_code == 200
        text = resp.data.decode("utf-8")
        assert f"The accounts and all data for {num_sources} sources" in text

        # simulate the source_deleter's work
        journalist_app_module.utils.purge_deleted_sources()

        # Make sure the collections are deleted from the filesystem
        def assertion():
            assert not (
                any(
                    [
                        os.path.exists(Storage.get_default().path(filesystem_id))
                        for filesystem_id in checkbox_values
                    ]
                )
            )

        utils.asynchronous.wait_for_assertion(assertion)


def _helper_filenames_submit(app):
    app.post(
        "/submit",
        data=dict(
            msg="This is a test.",
            fh=(BytesIO(b""), ""),
        ),
        follow_redirects=True,
    )
    app.post(
        "/submit",
        data=dict(
            msg="This is a test.",
            fh=(BytesIO(b"This is a test"), "test.txt"),
        ),
        follow_redirects=True,
    )
    app.post(
        "/submit",
        data=dict(
            msg="",
            fh=(BytesIO(b"This is a test"), "test.txt"),
        ),
        follow_redirects=True,
    )


def test_filenames(source_app, journalist_app, test_journo):
    """Test pretty, sequential filenames when source uploads messages
    and files"""
    # add a source and submit stuff
    with source_app.test_client() as app:
        app.post("/generate", data=GENERATE_DATA)
        tab_id = next(iter(session["codenames"].keys()))
        app.post("/create", data={"tab_id": tab_id})
        _helper_filenames_submit(app)

    # navigate to the collection page
    with journalist_app.test_client() as app:
        login_journalist(
            app, test_journo["username"], test_journo["password"], test_journo["otp_secret"]
        )
        resp = app.get("/")
        soup = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
        first_col_url = soup.select("table#collections tr.source > th.designation a")[0]["href"]
        resp = app.get(first_col_url)
        assert resp.status_code == 200

        # test filenames and sort order
        soup = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
        submission_filename_re = r"^{0}-[a-z0-9-_]+(-msg|-doc\.gz)\.gpg$"
        for i, submission_link in enumerate(
            soup.select("table#submissions tr.submission > th.filename a")
        ):
            filename = str(submission_link.contents[0])
            assert re.match(submission_filename_re.format(i + 1), filename)


def test_filenames_delete(journalist_app, source_app, test_journo):
    """Test pretty, sequential filenames when journalist deletes files"""
    # add a source and submit stuff
    with source_app.test_client() as app:
        app.post("/generate", data=GENERATE_DATA)
        tab_id = next(iter(session["codenames"].keys()))
        app.post("/create", data={"tab_id": tab_id})
        _helper_filenames_submit(app)

    # navigate to the collection page
    with journalist_app.test_client() as app:
        login_journalist(
            app, test_journo["username"], test_journo["password"], test_journo["otp_secret"]
        )
        resp = app.get("/")
        soup = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
        first_col_url = soup.select("table#collections tr.source > th.designation a")[0]["href"]
        resp = app.get(first_col_url)
        assert resp.status_code == 200
        soup = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

        # delete file #2
        _helper_filenames_delete(app, soup, 1)
        resp = app.get(first_col_url)
        soup = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

        # test filenames and sort order
        submission_filename_re = r"^{0}-[a-z0-9-_]+(-msg|-doc\.gz)\.gpg$"
        filename = str(
            soup.select("table#submissions tr.submission > th.filename a")[0].contents[0]
        )
        assert re.match(submission_filename_re.format(1), filename)
        filename = str(
            soup.select("table#submissions tr.submission > th.filename a")[1].contents[0]
        )
        assert re.match(submission_filename_re.format(3), filename)
        filename = str(
            soup.select("table#submissions tr.submission > th.filename a")[2].contents[0]
        )
        assert re.match(submission_filename_re.format(4), filename)


def test_user_change_password(journalist_app, test_journo):
    """Test that a journalist can successfully login after changing
    their password"""

    with journalist_app.test_client() as app:
        login_journalist(
            app, test_journo["username"], test_journo["password"], test_journo["otp_secret"]
        )
        # change password
        new_pw = "another correct horse battery staply long password"
        assert new_pw != test_journo["password"]  # precondition
        utils.prepare_password_change(app, test_journo["id"], new_pw)

        app.post(
            "/account/new-password",
            data=dict(
                password=new_pw,
                current_password=test_journo["password"],
                token=TOTP(test_journo["otp_secret"]).now(),
            ),
        )
        # logout
        resp = app.post("/logout")
        assert resp.status_code == 302

    # start a new client/context to be sure we've cleared the session
    with journalist_app.test_client() as app:
        # login with new credentials
        login_journalist(app, test_journo["username"], new_pw, test_journo["otp_secret"])


def test_prevent_document_uploads(source_app, journalist_app, test_admin):
    """Test that the source interface accepts only messages when
    allow_document_uploads == False.

    """

    # Set allow_document_uploads = False:
    with journalist_app.test_client() as app:
        login_journalist(
            app, test_admin["username"], test_admin["password"], test_admin["otp_secret"]
        )
        form = journalist_app_module.forms.SubmissionPreferencesForm(
            prevent_document_uploads=True, min_message_length=0
        )
        resp = app.post(
            "/admin/update-submission-preferences",
            data=form.data,
            follow_redirects=True,
        )
        assert resp.status_code == 200

    # Check that the source interface accepts only messages:
    with source_app.test_client() as app:
        app.post("/generate", data=GENERATE_DATA)
        tab_id = next(iter(session["codenames"].keys()))
        resp = app.post("/create", data={"tab_id": tab_id}, follow_redirects=True)
        assert resp.status_code == 200

        text = resp.data.decode("utf-8")
        soup = BeautifulSoup(text, "html.parser")
        assert "Submit Messages" in text
        assert len(soup.select('input[type="file"]')) == 0


def test_no_prevent_document_uploads(source_app, journalist_app, test_admin):
    """Test that the source interface accepts both files and messages when
    allow_document_uploads == True.

    """

    # Set allow_document_uploads = True:
    with journalist_app.test_client() as app:
        login_journalist(
            app, test_admin["username"], test_admin["password"], test_admin["otp_secret"]
        )
        form = journalist_app_module.forms.SubmissionPreferencesForm(
            prevent_document_uploads=False, min_message_length=0
        )
        resp = app.post(
            "/admin/update-submission-preferences",
            data=form.data,
            follow_redirects=True,
        )
        assert resp.status_code == 200

    # Check that the source interface accepts both files and messages:
    with source_app.test_client() as app:
        app.post("/generate", data=GENERATE_DATA)
        tab_id = next(iter(session["codenames"].keys()))
        resp = app.post("/create", data={"tab_id": tab_id}, follow_redirects=True)
        assert resp.status_code == 200

        text = resp.data.decode("utf-8")
        soup = BeautifulSoup(text, "html.parser")
        assert "Submit Files or Messages" in text
        assert len(soup.select('input[type="file"]')) == 1
