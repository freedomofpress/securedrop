#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import unittest

# Set environment variable so config.py uses a test environment
os.environ['SECUREDROP_ENV'] = 'test'

import config
import crypto_util
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

if __name__ == "__main__":
    unittest.main(verbosity=2)
