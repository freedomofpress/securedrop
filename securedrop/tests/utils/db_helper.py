# -*- coding: utf-8 -*-
"""Testing utilities that involve database (and often related
filesystem) interaction.
"""
import datetime
import math
import io
import os
import random
from typing import Dict, List

import mock
from flask import current_app

from db import db
from journalist_app.utils import mark_seen
from models import Journalist, Reply, SeenReply, Source, Submission
from passphrases import PassphraseGenerator
from sdconfig import config

os.environ['SECUREDROP_ENV'] = 'test'  # noqa


def init_journalist(first_name=None, last_name=None, is_admin=False):
    """Initialize a journalist into the database. Return their
    :class:`Journalist` object and password string.

    :param bool is_admin: Whether the user is an admin.

    :returns: A 2-tuple. The first entry, an :obj:`Journalist`
              corresponding to the row just added to the database. The
              second, their password string.
    """
    username = PassphraseGenerator.get_default().generate_passphrase()
    user_pw = PassphraseGenerator.get_default().generate_passphrase()
    user = Journalist(
        username=username,
        password=user_pw,
        first_name=first_name,
        last_name=last_name,
        is_admin=is_admin
    )
    db.session.add(user)
    db.session.commit()
    return user, user_pw


def delete_journalist(journalist):
    """Deletes a journalist from the database.

    :param Journalist journalist: The journalist to delete

    :returns: None
    """
    db.session.delete(journalist)
    db.session.commit()


def reply(journalist, source, num_replies):
    """Generates and submits *num_replies* replies to *source*
    from *journalist*. Returns reply objects as a list.

    :param Journalist journalist: The journalist to write the
                                     reply from.

    :param Source source: The source to send the reply to.

    :param int num_replies: Number of random-data replies to make.

    :returns: A list of the :class:`Reply`s submitted.
    """
    assert num_replies >= 1
    replies = []
    for _ in range(num_replies):
        source.interaction_count += 1
        fname = "{}-{}-reply.gpg".format(source.interaction_count,
                                         source.journalist_filename)
        current_app.crypto_util.encrypt(
            str(os.urandom(1)),
            [current_app.crypto_util.get_fingerprint(source.filesystem_id),
             config.JOURNALIST_KEY],
            current_app.storage.path(source.filesystem_id, fname))

        reply = Reply(journalist, source, fname)
        replies.append(reply)
        db.session.add(reply)
        db.session.flush()
        seen_reply = SeenReply(reply_id=reply.id, journalist_id=journalist.id)
        db.session.add(seen_reply)

    db.session.commit()
    return replies


def mock_verify_token(testcase):
    """Patch a :class:`unittest.TestCase` (or derivative class) so TOTP
    token verification always succeeds.

    :param unittest.TestCase testcase: The test case for which to patch
                                       TOTP verification.
    """
    patcher = mock.patch('Journalist.verify_token')
    testcase.addCleanup(patcher.stop)
    testcase.mock_journalist_verify_token = patcher.start()
    testcase.mock_journalist_verify_token.return_value = True


def mark_downloaded(*submissions):
    """Mark *submissions* as downloaded in the database.

    :param Submission submissions: One or more submissions that
                                      should be marked as downloaded.
    """
    for submission in submissions:
        submission.downloaded = True
    db.session.commit()


# {Source,Submission}

def init_source_without_keypair():
    """Initialize a source: create their database record and the
    filesystem directory that stores their submissions & replies.
    Return a source object and their codename string.

    :returns: A 2-tuple. The first entry, the :class:`Source`
    initialized. The second, their codename string.
    """
    # Create source identity and database record
    codename = PassphraseGenerator.get_default().generate_passphrase()
    filesystem_id = current_app.crypto_util.hash_codename(codename)
    journalist_filename = current_app.crypto_util.display_id()
    source = Source(filesystem_id, journalist_filename)
    db.session.add(source)
    db.session.commit()
    # Create the directory to store their submissions and replies
    os.mkdir(current_app.storage.path(source.filesystem_id))

    return source, codename


def init_source():
    """Initialize a source: create their database record, the
    filesystem directory that stores their submissions & replies,
    and their GPG key encrypted with their codename. Return a source
    object and their codename string.

    :returns: A 2-tuple. The first entry, the :class:`Source`
    initialized. The second, their codename string.
    """
    source, codename = init_source_without_keypair()
    current_app.crypto_util.genkeypair(source.filesystem_id, codename)

    return source, codename


def submit(source, num_submissions, submission_type="message"):
    """Generates and submits *num_submissions*
    :class:`Submission`s on behalf of a :class:`Source`
    *source*.

    :param Source source: The source on who's behalf to make
                             submissions.

    :param int num_submissions: Number of random-data submissions
                                to make.

    :returns: A list of the :class:`Submission`s submitted.
    """
    assert num_submissions >= 1
    source.last_updated = datetime.datetime.utcnow()
    db.session.add(source)
    submissions = []
    for _ in range(num_submissions):
        source.interaction_count += 1
        source.pending = False
        if submission_type == "file":
            fpath = current_app.storage.save_file_submission(
                source.filesystem_id,
                source.interaction_count,
                source.journalist_filename,
                "pipe.txt",
                io.BytesIO(b"Ceci n'est pas une pipe.")
            )
        else:
            fpath = current_app.storage.save_message_submission(
                source.filesystem_id,
                source.interaction_count,
                source.journalist_filename,
                str(os.urandom(1))
            )
        submission = Submission(source, fpath)
        submissions.append(submission)
        db.session.add(source)
        db.session.add(submission)

    db.session.commit()
    return submissions


def new_codename(client, session):
    """Helper function to go through the "generate codename" flow.
    """
    client.get('/generate')
    tab_id, codename = next(iter(session['codenames'].items()))
    client.post('/create', data={'tab_id': tab_id})
    return codename


def bulk_setup_for_seen_only(journo) -> List[Dict]:
    """
    Create some sources with some seen submissions that are not marked as 'downloaded' in the
    database and some seen replies from journo.
    """

    setup_collection = []

    for i in range(random.randint(2, 4)):
        collection = {}

        source, _ = init_source()

        submissions = submit(source, random.randint(2, 4))
        half = math.ceil(len(submissions) / 2)
        messages = submissions[half:]
        files = submissions[:half]
        replies = reply(journo, source, random.randint(1, 3))

        seen_files = random.sample(files, math.ceil(len(files) / 2))
        seen_messages = random.sample(messages, math.ceil(len(messages) / 2))
        seen_replies = random.sample(replies, math.ceil(len(replies) / 2))

        mark_seen(seen_files, journo)
        mark_seen(seen_messages, journo)
        mark_seen(seen_replies, journo)

        unseen_files = list(set(files).difference(set(seen_files)))
        unseen_messages = list(set(messages).difference(set(seen_messages)))
        unseen_replies = list(set(replies).difference(set(seen_replies)))
        not_downloaded = list(set(files + messages).difference(set(seen_files + seen_messages)))

        collection['source'] = source
        collection['seen_files'] = seen_files
        collection['seen_messages'] = seen_messages
        collection['seen_replies'] = seen_replies
        collection['unseen_files'] = unseen_files
        collection['unseen_messages'] = unseen_messages
        collection['unseen_replies'] = unseen_replies
        collection['not_downloaded'] = not_downloaded

        setup_collection.append(collection)

    return setup_collection
