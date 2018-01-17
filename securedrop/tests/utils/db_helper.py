# -*- coding: utf-8 -*-
"""Testing utilities that involve database (and often related
filesystem) interaction.
"""
import mock
import os

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
import config
import crypto_util
import db
import store

# db.{Journalist, Reply}


def init_journalist(is_admin=False):
    """Initialize a journalist into the database. Return their
    :class:`db.Journalist` object and password string.

    :param bool is_admin: Whether the user is an admin.

    :returns: A 2-tuple. The first entry, an :obj:`db.Journalist`
              corresponding to the row just added to the database. The
              second, their password string.
    """
    username = crypto_util.genrandomid()
    user_pw = crypto_util.genrandomid()
    user = db.Journalist(username, user_pw, is_admin)
    db.db_session.add(user)
    db.db_session.commit()
    return user, user_pw


def reply(journalist, source, num_replies):
    """Generates and submits *num_replies* replies to *source*
    from *journalist*. Returns reply objects as a list.

    :param db.Journalist journalist: The journalist to write the
                                     reply from.

    :param db.Source source: The source to send the reply to.

    :param int num_replies: Number of random-data replies to make.

    :returns: A list of the :class:`db.Reply`s submitted.
    """
    assert num_replies >= 1
    replies = []
    for _ in range(num_replies):
        source.interaction_count += 1
        fname = "{}-{}-reply.gpg".format(source.interaction_count,
                                         source.journalist_filename)
        crypto_util.encrypt(str(os.urandom(1)),
                            [
                                crypto_util.getkey(source.filesystem_id),
                                config.JOURNALIST_KEY
                            ],
                            store.path(source.filesystem_id, fname))
        reply = db.Reply(journalist, source, fname)
        replies.append(reply)
        db.db_session.add(reply)

    db.db_session.commit()
    return replies


def mock_verify_token(testcase):
    """Patch a :class:`unittest.TestCase` (or derivative class) so TOTP
    token verification always succeeds.

    :param unittest.TestCase testcase: The test case for which to patch
                                       TOTP verification.
    """
    patcher = mock.patch('db.Journalist.verify_token')
    testcase.addCleanup(patcher.stop)
    testcase.mock_journalist_verify_token = patcher.start()
    testcase.mock_journalist_verify_token.return_value = True


def mark_downloaded(*submissions):
    """Mark *submissions* as downloaded in the database.

    :param db.Submission submissions: One or more submissions that
                                      should be marked as downloaded.
    """
    for submission in submissions:
        submission.downloaded = True
    db.db_session.commit()


# db.{Source,Submission}

def init_source_without_keypair():
    """Initialize a source: create their database record and the
    filesystem directory that stores their submissions & replies.
    Return a source object and their codename string.

    :returns: A 2-tuple. The first entry, the :class:`db.Source`
    initialized. The second, their codename string.
    """
    # Create source identity and database record
    codename = crypto_util.genrandomid()
    filesystem_id = crypto_util.hash_codename(codename)
    journalist_filename = crypto_util.display_id()
    source = db.Source(filesystem_id, journalist_filename)
    db.db_session.add(source)
    db.db_session.commit()
    # Create the directory to store their submissions and replies
    os.mkdir(store.path(source.filesystem_id))

    return source, codename


def init_source():
    """Initialize a source: create their database record, the
    filesystem directory that stores their submissions & replies,
    and their GPG key encrypted with their codename. Return a source
    object and their codename string.

    :returns: A 2-tuple. The first entry, the :class:`db.Source`
    initialized. The second, their codename string.
    """
    source, codename = init_source_without_keypair()
    crypto_util.genkeypair(source.filesystem_id, codename)

    return source, codename


def submit(source, num_submissions):
    """Generates and submits *num_submissions*
    :class:`db.Submission`s on behalf of a :class:`db.Source`
    *source*.

    :param db.Source source: The source on who's behalf to make
                             submissions.

    :param int num_submissions: Number of random-data submissions
                                to make.

    :returns: A list of the :class:`db.Submission`s submitted.
    """
    assert num_submissions >= 1
    submissions = []
    for _ in range(num_submissions):
        source.interaction_count += 1
        fpath = store.save_message_submission(source.filesystem_id,
                                              source.interaction_count,
                                              source.journalist_filename,
                                              str(os.urandom(1)))
        submission = db.Submission(source, fpath)
        submissions.append(submission)
        db.db_session.add(submission)

    db.db_session.commit()
    return submissions


def new_codename(client, session):
    """Helper function to go through the "generate codename" flow.
    """
    # clear the session because our tests have implicit reliance on each other
    session.clear()

    client.get('/generate')
    codename = session['codename']
    client.post('/create')
    return codename
