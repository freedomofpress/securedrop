import base64
import binascii
import secrets
from datetime import datetime
from typing import Optional

from cryptography.hazmat.primitives.hashes import SHA1
from cryptography.hazmat.primitives.twofactor import InvalidToken, hotp, totp


def random_base32(length: int = 32) -> str:
    if length < 32:
        raise ValueError("Secrets should be at least 160 bits")

    chars_to_use = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")
    return "".join(secrets.choice(chars_to_use) for _ in range(length))


class OtpSecretInvalid(Exception):
    """Raised when a user's OTP secret is invalid - for example, too short"""


class OtpTokenInvalid(Exception):
    pass


class HOTP:

    # Current parameters for HOTP
    _LENGTH = 6

    # nosemgrep: python.cryptography.security.insecure-hash-algorithms.insecure-hash-algorithm-sha1
    _ALGORITHM = SHA1()  # noqa: S303

    _LOOK_AHEAD_WINDOW_SIZE = 20

    _SECRET_BASE32_LENGTH = 32  # 160 bits == 40 hex digits (== 32 ascii-encoded chars in db)
    SECRET_HEX_LENGTH = 40  # Required length for hex-format HOTP secrets as input by users

    def __init__(self, secret_as_base32: str) -> None:
        if len(secret_as_base32) != self._SECRET_BASE32_LENGTH:
            raise OtpSecretInvalid("Invalid secret length")

        try:
            otp_secret_as_bytes = base64.b32decode(
                # Need casefold=True because the base32 secret we receive from the UI might be
                # lowercase
                secret_as_base32,
                casefold=True,
            )
        except binascii.Error:
            raise OtpSecretInvalid("Secret is not base32-encoded")

        self._hotp = hotp.HOTP(
            key=otp_secret_as_bytes,
            length=self._LENGTH,
            algorithm=self._ALGORITHM,
        )

    def generate(self, counter: int) -> str:
        return self._hotp.generate(counter).decode("ascii")

    def verify(self, token: str, counter: int) -> int:
        """Validate an HOTP-generated token and return the counter value that succeeded."""
        counter_value_that_succeeded: Optional[int] = None
        for counter_value in range(counter, counter + self._LOOK_AHEAD_WINDOW_SIZE):
            try:
                self._hotp.verify(token.encode("ascii"), counter_value)
                counter_value_that_succeeded = counter_value
                break
            except InvalidToken:
                pass

        if counter_value_that_succeeded is None:
            raise OtpTokenInvalid("Token verification failed")

        return counter_value_that_succeeded


class TOTP:

    # Current parameters for TOTP
    _LENGTH = 6
    _TIME_STEP = 30

    # nosemgrep: python.cryptography.security.insecure-hash-algorithms.insecure-hash-algorithm-sha1
    _ALGORITHM = SHA1()  # noqa: S303

    # Minimum length for ascii-encoded OTP secrets - by default, secrets are now 160-bit (32 chars)
    # but existing Journalist users may still have 80-bit (16-char) secrets
    _SECRET_MIN_BASE32_LENGTH = 16  # 80 bits == 40 hex digits (== 16 ascii-encoded chars in db)

    def __init__(self, secret_as_base32: str) -> None:
        if len(secret_as_base32) < self._SECRET_MIN_BASE32_LENGTH:
            raise OtpSecretInvalid("Invalid secret length")

        try:
            otp_secret_as_bytes = base64.b32decode(
                # Need casefold=True because the base32 secret we receive from the UI might be
                # lowercase
                secret_as_base32,
                casefold=True,
            )
        except binascii.Error:
            raise OtpSecretInvalid("Secret is not base32-encoded")

        self._totp = totp.TOTP(
            key=otp_secret_as_bytes,
            length=self._LENGTH,
            algorithm=self._ALGORITHM,
            time_step=self._TIME_STEP,
            # Existing Journalist users may still have 80-bit (16-char) secrets
            enforce_key_length=False,
        )

    def generate(self, time: datetime) -> str:
        return self._totp.generate(time.timestamp()).decode("ascii")

    def now(self) -> str:
        return self._totp.generate(datetime.utcnow().timestamp()).decode("ascii")

    def verify(self, token: str, time: datetime) -> None:
        # Also check the given token against the previous and next valid tokens, to compensate
        # for potential time skew between the client and the server. The total valid window is 1:30s
        token_verification_succeeded = False
        for index_for_time_skew in [-1, 0, 1]:
            time_for_time_skew = int(time.timestamp()) + self._TIME_STEP * index_for_time_skew
            try:
                self._totp.verify(token.encode("ascii"), time_for_time_skew)
                token_verification_succeeded = True
                break
            except InvalidToken:
                pass

        if not token_verification_succeeded:
            raise OtpTokenInvalid("Token verification failed")

    def get_provisioning_uri(self, account_name: str) -> str:
        return self._totp.get_provisioning_uri(account_name=account_name, issuer="SecureDrop")
