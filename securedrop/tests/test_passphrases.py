from unittest import mock

import pytest

from passphrases import PassphraseGenerator, InvalidWordListError

# pylint: disable=unsupported-membership-test
# False positive https://github.com/PyCQA/pylint/issues/3045


class TestPassphrasesGenerator:
    def test_default_generator(self):
        # Given the default generator for the Securedrop app
        generator = PassphraseGenerator.get_default()
        assert generator.available_languages == {"en", "fr"}

        # When using it to generate a passphrase
        # It succeeds
        passphrase = generator.generate_passphrase()

        # And a reasonably-secure passphrase was generated
        assert passphrase
        assert len(passphrase) >= 20
        assert len(passphrase.split(" ")) >= 7

    def test_default_generator_passphrases_are_random(self):
        # Given the default generator for the Securedrop app
        generator = PassphraseGenerator.get_default()

        # When using it to generate two passphrases
        # It succeeds
        passphrase1 = generator.generate_passphrase()
        passphrase2 = generator.generate_passphrase()

        # And the two passphrases are different because they are randomly-generated
        assert passphrase1 != passphrase2

    @mock.patch.object(PassphraseGenerator, "_WORD_LIST_MINIMUM_SIZE", 1)
    def test_generate_passphrase_with_specific_language(self):
        # Given a generator that supports two languages
        generator = PassphraseGenerator(language_to_words={"en": ["boat"], "fr": ["bateau"]})
        assert generator.available_languages == {"en", "fr"}

        # When using it to create a passphrase for one of the two languages
        # It succeeds
        passphrase = generator.generate_passphrase(preferred_language="fr")

        # And the passphrase is in the chosen language
        assert "bateau" in passphrase
        assert "boat" not in passphrase

    @mock.patch.object(PassphraseGenerator, "_WORD_LIST_MINIMUM_SIZE", 1)
    def test_generate_passphrase_with_specific_language_that_is_not_available(self):
        # Given a generator that supports two languages
        generator = PassphraseGenerator(
            language_to_words={"en": ["boat"], "fr": ["bateau"]},
            # With english as the fallback language
            fallback_language="en",
        )
        assert generator.available_languages == {"en", "fr"}

        # When using it to create a passphrase for another, non-supported language
        # It succeeds
        passphrase = generator.generate_passphrase(preferred_language="es")

        # And the passphrase is in the default/fallback language, english
        assert "boat" in passphrase
        assert "bateau" not in passphrase

    def test_word_list_does_not_have_enough_words(self):
        with pytest.raises(InvalidWordListError, match="long-enough words"):
            PassphraseGenerator(language_to_words={"en": ["only", "three", "words"]})

    @mock.patch.object(PassphraseGenerator, "_WORD_LIST_MINIMUM_SIZE", 1)
    def test_word_list_will_generate_overly_long_passphrase(self):
        with pytest.raises(InvalidWordListError, match="over the maximum length"):
            PassphraseGenerator(language_to_words={"en": ["overlylongwordtogetoverthelimit"]})

    @mock.patch.object(PassphraseGenerator, "_WORD_LIST_MINIMUM_SIZE", 1)
    def test_word_list_will_generate_overly_short_passphrase(self):
        with pytest.raises(InvalidWordListError, match="under the minimum length"):
            PassphraseGenerator(language_to_words={"en": ["b", "a"]})

    @mock.patch.object(PassphraseGenerator, "_WORD_LIST_MINIMUM_SIZE", 1)
    def test_word_list_has_non_ascii_string(self):
        with pytest.raises(InvalidWordListError, match="non-ASCII words"):
            PassphraseGenerator(language_to_words={"en": ["word", "éoèô"]})
