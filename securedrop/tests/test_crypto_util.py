# -*- coding: utf-8 -*-
import os
import unittest

os.environ['SECUREDROP_ENV'] = 'test'
import config
import crypto_util
import store
import utils


class TestCryptoUtil(unittest.TestCase):

    """The set of tests for crypto_util.py."""

    def setUp(self):
        utils.env.setup()

    def tearDown(self):
        utils.env.teardown()

    def test_clean(self):
        with self.assertRaises(crypto_util.CryptoException):
            crypto_util.clean('foo bar`') # backtick is not currently allowed
        with self.assertRaises(crypto_util.CryptoException):
            crypto_util.clean('bar baz~') # tilde is not currently allowed

    def test_encrypt_success(self):
        source, _ = utils.db_helper.init_source()
        encrypted = crypto_util.encrypt(str(os.urandom(1)),
                                        [
                                            crypto_util.getkey(source.filesystem_id),
                                            config.JOURNALIST_KEY
                                        ],
                                        store.path(source.filesystem_id, 'somefile.gpg'))
        self.assertGreater(len(encrypted), 0)

    def test_encrypt_failure(self):
        source, _ = utils.db_helper.init_source()
        with self.assertRaisesRegexp(crypto_util.CryptoException,
                                     'no terminal at all requested'):
            encrypted = crypto_util.encrypt(str(os.urandom(1)),
                                            [
                                            ],
                                            store.path(source.filesystem_id, 'other.gpg'))
