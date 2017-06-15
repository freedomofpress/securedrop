# -*- coding: utf-8 -*-
import os
import unittest

os.environ['SECUREDROP_ENV'] = 'test'
import config
import crypto_util
import db
import store
import utils

class TestCryptoUtil(unittest.TestCase):
    """The set of tests for crypto_util.py.
    """

    def setUp(self):
        utils.env.setup()

    def tearDown(self):
        utils.env.teardown()

    def test_word_lists_imports(self):
        """Make sure word count for each list is correct and Guard
        against regressions regarding not stripping file contents
        correctly.
        """
        words = crypto_util.words
        nouns = crypto_util.nouns
        adjectives = crypto_util.adjectives
        self.assertEqual(len(words), 7603)
        self.assertEqual(len(adjectives), 8222)
        self.assertEqual(len(nouns), 17949)
        self.assertNotIn('', words + nouns + adjectives)

    def test_genrandomid_result_cannot_exceed_max_codename_len(self):
        """It should be impossible to generate an id longer than
        :attr:`db.Source.MAX_CODENAME_LENGTH` using the default number
        of words `crypto_util.NUM_CODENAME_WORDS`.
        """
        longest_word_len = max([len(word) for word in crypto_util.words])
        longest_codename_len = len(' '.join(
            ['_' * longest_word_len
             for _ in xrange(crypto_util.NUM_CODENAME_WORDS)]))
        self.assertLessEqual(longest_codename_len,
                             db.Source.MAX_CODENAME_LEN)

    def test_clean(self):
        ok = (' !#%$&)(+*-1032547698;:=?@acbedgfihkjmlonqpsrutwvyxzABCDEFGHIJ'
              'KLMNOPQRSTUVWXYZ')
        invalid_1 = 'foo bar`'
        invalid_2 = 'bar baz~'

        self.assertEqual(ok, crypto_util.clean(ok))
        with self.assertRaisesRegexp(crypto_util.CryptoException,
                                   'invalid input: {}'.format(invalid_1)):
            crypto_util.clean(invalid_1)
        with self.assertRaisesRegexp(crypto_util.CryptoException,
                                   'invalid input: {}'.format(invalid_2)):
            crypto_util.clean(invalid_2)

    def test_encrypt_success(self):
        source, _ = utils.db_helper.init_source()
        message = str(os.urandom(1))
        ciphertext = crypto_util.encrypt(
            message,
            [crypto_util.getkey(source.filesystem_id), config.JOURNALIST_KEY],
            store.path(source.filesystem_id, 'somefile.gpg'))

        self.assertIsInstance(ciphertext, str)
        self.assertNotEqual(ciphertext, message)
        self.assertGreater(len(ciphertext), 0)

    def test_encrypt_failure(self):
        source, _ = utils.db_helper.init_source()
        with self.assertRaisesRegexp(crypto_util.CryptoException,
                                     'no terminal at all requested'):
            crypto_util.encrypt(
                str(os.urandom(1)),
                [],
                store.path(source.filesystem_id, 'other.gpg'))

    def test_encrypt_without_output(self):
        """We simply do not specify the option output keyword argument
        to crypto_util.encrypt() here in order to confirm encryption
        works when it defaults to `None`.
        """
        source, codename = utils.db_helper.init_source()
        message = str(os.urandom(1))
        ciphertext = crypto_util.encrypt(
            message,
            [crypto_util.getkey(source.filesystem_id), config.JOURNALIST_KEY])
        plaintext = crypto_util.decrypt(codename, ciphertext)

        self.assertEqual(message, plaintext)

    def test_encrypt_binary_stream(self):
        """Generally, we pass unicode strings (the type form data is
        returned as) as plaintext to crypto_util.encrypt(). These have
        to be converted to "binary stream" types (such as `file`) before
        we can actually call gnupg.GPG.encrypt() on them. This is done
        in crypto_util.encrypt() with an `if` branch that uses
        `gnupg._util._is_stream(plaintext)` as the predicate, and calls
        `gnupg._util._make_binary_stream(plaintext)` if necessary. This
        test ensures our encrypt function works even if we provide
        inputs such that this `if` branch is skipped (i.e., the object
        passed for `plaintext` is one such that
        `gnupg._util._is_stream(plaintext)` returns `True`).
        """
        source, codename = utils.db_helper.init_source()
        with open(os.path.realpath(__file__)) as fh:
            ciphertext = crypto_util.encrypt(
                fh,
                [crypto_util.getkey(source.filesystem_id),
                 config.JOURNALIST_KEY],
                store.path(source.filesystem_id, 'somefile.gpg'))
        plaintext = crypto_util.decrypt(codename, ciphertext)

        with open(os.path.realpath(__file__)) as fh:
            self.assertEqual(fh.read(), plaintext)

    def test_encrypt_fingerprints_not_a_list_or_tuple(self):
        """If passed a single fingerprint as a string, encrypt should
        correctly place that string in a list, and encryption/
        decryption should work as intended."""
        source, codename = utils.db_helper.init_source()
        message = str(os.urandom(1))
        ciphertext = crypto_util.encrypt(
            message,
            crypto_util.getkey(source.filesystem_id),
            store.path(source.filesystem_id, 'somefile.gpg'))
        plaintext = crypto_util.decrypt(codename, ciphertext)

        self.assertEqual(message, plaintext)

    def test_basic_encrypt_then_decrypt_multiple_recipients(self):
        source, codename = utils.db_helper.init_source()
        message = str(os.urandom(1))
        ciphertext = crypto_util.encrypt(
            message,
            [crypto_util.getkey(source.filesystem_id),
             config.JOURNALIST_KEY],
            store.path(source.filesystem_id, 'somefile.gpg'))
        plaintext = crypto_util.decrypt(codename, ciphertext)

        self.assertEqual(message, plaintext)

        # Since there's no way to specify which key to use for
        # decryption to python-gnupg, we delete the `source`'s key and
        # ensure we can decrypt with the `config.JOURNALIST_KEY`.
        crypto_util.delete_reply_keypair(source.filesystem_id)
        plaintext_ = crypto_util.gpg.decrypt(ciphertext).data

        self.assertEqual(message, plaintext_)

    def test_genrandomid(self):
        id = crypto_util.genrandomid()
        id_words = id.split()

        self.assertEqual(id, crypto_util.clean(id))
        self.assertEqual(len(id_words), crypto_util.NUM_CODENAME_WORDS)
        for word in id_words:
            self.assertIn(word, crypto_util.words)

    def test_display_id(self):
        id = crypto_util.display_id()
        id_words = id.split()

        self.assertEqual(len(id_words), 2)
        self.assertIn(id_words[0], crypto_util.adjectives)
        self.assertIn(id_words[1], crypto_util.nouns)

    def test_hash_codename(self):
        codename = crypto_util.genrandomid()
        hashed_codename = crypto_util.hash_codename(codename)

        self.assertRegexpMatches(hashed_codename, '^[2-7A-Z]{103}=$')

    def test_genkeypair(self):
        codename = crypto_util.genrandomid()
        filesystem_id = crypto_util.hash_codename(codename)
        journalist_filename = crypto_util.display_id()
        source = db.Source(filesystem_id, journalist_filename)
        db.db_session.add(source)
        db.db_session.commit()
        crypto_util.genkeypair(source.filesystem_id, codename)

        self.assertIsNotNone(crypto_util.getkey(filesystem_id))

    def test_delete_reply_keypair(self):
        source, _ = utils.db_helper.init_source()
        crypto_util.delete_reply_keypair(source.filesystem_id)

        self.assertIsNone(crypto_util.getkey(source.filesystem_id))

    def test_delete_reply_keypair_no_key(self):
        """No exceptions should be raised when provided a filesystem id that
        does not exist.
        """
        crypto_util.delete_reply_keypair('Reality Winner')

    def test_getkey(self):
        source, _ = utils.db_helper.init_source()

        self.assertIsNotNone(crypto_util.getkey(source.filesystem_id))
