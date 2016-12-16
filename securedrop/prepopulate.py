#!/usr/bin/env python

import base64
import binascii

import factory

from db import db_session, Journalist, Reply, Source, Submission
import crypto_util


def get_filesystem_id():
    return crypto_util.hash_codename(crypto_util.genrandomid())

def get_journalist_designation():
    return crypto_util.display_id()


class SourceFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory to generate sources and trigger Submissions and Replies to
    get loaded in
    """
    class Meta:
        model = Source
        sqlalchemy_session = db_session

    #@factory.lazy_attribute_sequence
    filesystem_id = factory.Sequence(lambda o: get_filesystem_id())
    #filesystem_id = get_filesystem_id()
    #journalist_designation = factory.Sequence(lambda o: get_journalist_designation())
    #journalist_designation = get_journalist_designation()
    journalist_designation = factory.LazyFunction(get_journalist_designation())

    @factory.post_generation
    def generate_source_key(self, filesystem_id, journalist_designation):
        crypto_util.genkeypair(filesystem_id, journalist_designation)

    #factory.RelatedFactory(SubmissionFactory, 'submission',
    #                       action=Submission.ACTION_CREATE)


class SubmissionFactory(factory.alchemy.SQLAlchemyModelFactory):
    """
    files = ['1-abc1-msg.gpg', '2-abc2-msg.gpg']
    filenames = common.setup_test_docs(sid, files)
    """
    pass

class ReplyFactory(factory.alchemy.SQLAlchemyModelFactory):
    """
    files = ['1-def-reply.gpg', '2-def-reply.gpg']
    filenames = common.setup_test_replies(source.filesystem_id,
                                          self.user.id,
                                          files)
    """
    pass


def add_test_data():
    # Add administrator
    admin = Journalist(
        username='test_admin',
        password='gravity defame',
        is_admin=True,
        otp_secret=binascii.hexlify(base64.b32decode('XJK6TLUZRL627I6U'))
        )
    db_session.add(admin)
    db_session.commit()

    # Add Journalist
    journo = Journalist(
        username='test_journo',
        password='retread hash',
        is_admin=False,
        otp_secret=binascii.hexlify(base64.b32decode('TIPQKYZRTV7W7ZWB'))
        )
    db_session.add(journo)
    db_session.commit()

    # Add some documents, submissions, and replies for 10 sources
    sources = SourceFactory.create_batch(size=10)
    db_session.add_all(sources)
    db_session.commit()


if __name__ == '__main__':
    add_test_data()
