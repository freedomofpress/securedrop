from datetime import datetime

import pytest
from two_factor import HOTP, TOTP, OtpSecretInvalid, OtpTokenInvalid


class TestHOTP:
    _SECRET = "YQTEGUTJCMBETH3KUUZZMRWZAVBKGT5O"
    _VALID_TOKEN = "464263"
    _VALID_TOKEN_COUNTER = 12

    def test_invalid_secret_wrong_length(self) -> None:
        with pytest.raises(OtpSecretInvalid, match="length"):
            TOTP(secret_as_base32="JHCOGO7VCER3EJ")

    def test_invalid_secret_not_base32(self) -> None:
        with pytest.raises(OtpSecretInvalid, match="base32"):
            TOTP(secret_as_base32="not actually &&&!!! base 32")

    def test_generate(self) -> None:
        # Given a HOTP validator
        hotp = HOTP(secret_as_base32=self._SECRET)

        # When generating a token with the corresponding counter value
        # Then it succeeds
        token = hotp.generate(counter=self._VALID_TOKEN_COUNTER)

        # And the expected token is returned
        assert token == self._VALID_TOKEN

    def test_verify(self) -> None:
        # Given a HOTP validator and a token it generated
        hotp = HOTP(secret_as_base32=self._SECRET)

        # When verifying a token with the corresponding counter value
        counter = self._VALID_TOKEN_COUNTER

        # Then it succeeds
        hotp.verify(self._VALID_TOKEN, counter)

    def test_verify_within_look_ahead_window(self) -> None:
        # Given a HOTP validator and a token it generated
        hotp = HOTP(secret_as_base32=self._SECRET)

        # When verifying a token with the a counter value that is slightly off but within
        # the look-ahead window
        counter = self._VALID_TOKEN_COUNTER - 10

        # Then it succeeds
        hotp.verify(self._VALID_TOKEN, counter)

    @pytest.mark.parametrize(
        ("token", "counter"),
        [
            pytest.param(_VALID_TOKEN, _VALID_TOKEN_COUNTER + 10),
            pytest.param(_VALID_TOKEN, 12345),
        ],
    )
    def test_verify_but_token_invalid(self, token: str, counter: int) -> None:
        # Given a HOTP validator and a token
        hotp = HOTP(secret_as_base32=self._SECRET)

        # When verifying the token with an invalid value or counter, then it fails
        with pytest.raises(OtpTokenInvalid):
            hotp.verify(token, counter)


class TestTOTP:
    _SECRET = "JHCOGO7VCER3EJ4L"
    _VALID_TOKEN = "705334"
    _VALID_TOKEN_GENERATED_AT = 1666515039

    def test_invalid_secret_wrong_length(self) -> None:
        with pytest.raises(OtpSecretInvalid, match="length"):
            TOTP(secret_as_base32="JHCOGO7")

    def test_invalid_secret_not_base32(self) -> None:
        with pytest.raises(OtpSecretInvalid, match="base32"):
            TOTP(secret_as_base32="not actually &&&!!! base 32")

    def test_invalid_secret(self) -> None:
        with pytest.raises(OtpSecretInvalid):
            TOTP(secret_as_base32="invalid_secret")

    def test_get_provisioning_uri(self) -> None:
        totp = TOTP(secret_as_base32=self._SECRET)
        assert totp.get_provisioning_uri("account")

    def test_generate(self) -> None:
        # Given a TOTP validator
        totp = TOTP(secret_as_base32=self._SECRET)

        # When generating a token at a specific time
        generation_time = datetime.fromtimestamp(self._VALID_TOKEN_GENERATED_AT)

        # Then it succeeds
        token = totp.generate(generation_time)

        # And the expected token is returned
        assert token == self._VALID_TOKEN

    @pytest.mark.parametrize(
        ("token", "verification_timestamp"),
        [
            # Ensure the token is valid at the exact time
            pytest.param(_VALID_TOKEN, _VALID_TOKEN_GENERATED_AT),
            # And at the previous & following time windows
            pytest.param(_VALID_TOKEN, _VALID_TOKEN_GENERATED_AT - 30),
            pytest.param(_VALID_TOKEN, _VALID_TOKEN_GENERATED_AT + 30),
        ],
    )
    def test_verify(self, token: str, verification_timestamp: int) -> None:
        # Given a TOTP validator and a token it generated
        totp = TOTP(secret_as_base32=self._SECRET)

        # And the verification time is within the time window when the token is considered valid
        verification_time = datetime.fromtimestamp(verification_timestamp)

        # When verifying the token, then it succeeds
        totp.verify(token, verification_time)

    @pytest.mark.parametrize(
        ("token", "verification_timestamp"),
        [
            # Ensure the token is invalid at a totally wrong time
            pytest.param(_VALID_TOKEN, 123456),
            # And at times that are very close to the valid time windows
            pytest.param(_VALID_TOKEN, _VALID_TOKEN_GENERATED_AT - 60),
            pytest.param(_VALID_TOKEN, _VALID_TOKEN_GENERATED_AT + 60),
        ],
    )
    def test_verify_but_token_invalid(self, token: str, verification_timestamp: int) -> None:
        # Given a TOTP validator and a token it generated
        totp = TOTP(secret_as_base32=self._SECRET)

        # And the verification time is within the time window when the token is considered NOT valid
        verification_time = datetime.fromtimestamp(verification_timestamp)

        # When verifying the token, then it fails
        with pytest.raises(OtpTokenInvalid):
            totp.verify(token, verification_time)
