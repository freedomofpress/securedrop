# -*- coding: utf-8 -*-
import base64
import binascii
import datetime
import os
import uuid
from io import BytesIO
from logging import Logger
from typing import Any, Callable, Dict, List, Optional, Union

import pyotp
import qrcode

# Using svg because it doesn't require additional dependencies
import qrcode.image.svg
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf import scrypt
from db import db
from encryption import EncryptionManager, GpgKeyNotFoundError
from flask import url_for
from flask_babel import gettext, ngettext
from markupsafe import Markup
from passlib.hash import argon2
from passphrases import PassphraseGenerator
from pyotp import HOTP, TOTP
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, backref, relationship
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from store import Storage

_default_instance_config: Optional["InstanceConfig"] = None

LOGIN_HARDENING = True
if os.environ.get("SECUREDROP_ENV") == "test":
    LOGIN_HARDENING = False

ARGON2_PARAMS = dict(memory_cost=2**16, rounds=4, parallelism=2)

# Required length for hex-format HOTP secrets as input by users
HOTP_SECRET_LENGTH = 40  # 160 bits == 40 hex digits (== 32 ascii-encoded chars in db)

# Minimum length for ascii-encoded OTP secrets - by default, secrets are now 160-bit (32 chars)
# but existing Journalist users may still have 80-bit (16-char) secrets
OTP_SECRET_MIN_ASCII_LENGTH = 16  # 80 bits == 40 hex digits (== 16 ascii-encoded chars in db)


def get_one_or_else(
    query: Query, logger: "Logger", failure_method: "Callable[[int], None]"
) -> db.Model:
    try:
        return query.one()
    except MultipleResultsFound as e:
        logger.error(
            "Found multiple while executing %s when one was expected: %s"
            % (
                query,
                e,
            )
        )
        failure_method(500)
    except NoResultFound as e:
        logger.error("Found none when one was expected: %s" % (e,))
        failure_method(404)


class Source(db.Model):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True, nullable=False)
    filesystem_id = Column(String(96), unique=True, nullable=False)
    journalist_designation = Column(String(255), nullable=False)
    last_updated = Column(DateTime)
    star = relationship("SourceStar", uselist=False, backref="source")

    # sources are "pending" and don't get displayed to journalists until they
    # submit something
    pending = Column(Boolean, default=True)

    # keep track of how many interactions have happened, for filenames
    interaction_count = Column(Integer, default=0, nullable=False)

    # when deletion of the source was requested
    deleted_at = Column(DateTime)

    def __init__(self, filesystem_id: str, journalist_designation: str) -> None:
        self.filesystem_id = filesystem_id
        self.journalist_designation = journalist_designation
        self.uuid = str(uuid.uuid4())

    def __repr__(self) -> str:
        return "<Source %r>" % (self.journalist_designation)

    @property
    def journalist_filename(self) -> str:
        valid_chars = "abcdefghijklmnopqrstuvwxyz1234567890-_"
        return "".join(
            [c for c in self.journalist_designation.lower().replace(" ", "_") if c in valid_chars]
        )

    def documents_messages_count(self) -> "Dict[str, int]":
        self.docs_msgs_count = {"messages": 0, "documents": 0}
        for submission in self.submissions:
            if submission.is_message:
                self.docs_msgs_count["messages"] += 1
            elif submission.is_file:
                self.docs_msgs_count["documents"] += 1
        return self.docs_msgs_count

    @property
    def collection(self) -> "List[Union[Submission, Reply]]":
        """Return the list of submissions and replies for this source, sorted
        in ascending order by the filename/interaction count."""
        collection = []  # type: List[Union[Submission, Reply]]
        collection.extend(self.submissions)
        collection.extend(self.replies)
        collection.sort(key=lambda x: int(x.filename.split("-")[0]))
        return collection

    @property
    def fingerprint(self) -> "Optional[str]":
        try:
            return EncryptionManager.get_default().get_source_key_fingerprint(self.filesystem_id)
        except GpgKeyNotFoundError:
            return None

    @property
    def public_key(self) -> "Optional[str]":
        try:
            return EncryptionManager.get_default().get_source_public_key(self.filesystem_id)
        except GpgKeyNotFoundError:
            return None

    def to_json(self) -> "Dict[str, object]":
        docs_msg_count = self.documents_messages_count()

        if self.last_updated:
            last_updated = self.last_updated
        else:
            last_updated = datetime.datetime.now(tz=datetime.timezone.utc)

        if self.star and self.star.starred:
            starred = True
        else:
            starred = False

        json_source = {
            "uuid": self.uuid,
            "url": url_for("api.single_source", source_uuid=self.uuid),
            "journalist_designation": self.journalist_designation,
            "is_flagged": False,
            "is_starred": starred,
            "last_updated": last_updated,
            "interaction_count": self.interaction_count,
            "key": {
                "type": "PGP",
                "public": self.public_key,
                "fingerprint": self.fingerprint,
            },
            "number_of_documents": docs_msg_count["documents"],
            "number_of_messages": docs_msg_count["messages"],
            "submissions_url": url_for("api.all_source_submissions", source_uuid=self.uuid),
            "add_star_url": url_for("api.add_star", source_uuid=self.uuid),
            "remove_star_url": url_for("api.remove_star", source_uuid=self.uuid),
            "replies_url": url_for("api.all_source_replies", source_uuid=self.uuid),
        }
        return json_source


class Submission(db.Model):
    MAX_MESSAGE_LEN = 100000

    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True, nullable=False)
    source_id = Column(Integer, ForeignKey("sources.id"))
    source = relationship("Source", backref=backref("submissions", order_by=id, cascade="delete"))

    filename = Column(String(255), nullable=False)
    size = Column(Integer, nullable=False)
    downloaded = Column(Boolean, default=False)
    """
    The checksum of the encrypted file on disk.
    Format: $hash_name:$hex_encoded_hash_value
    Example: sha256:05fa5efd7d1b608ac1fbdf19a61a5a439d05b05225e81faa63fdd188296b614a
    """
    checksum = Column(String(255))

    def __init__(self, source: Source, filename: str, storage: Storage) -> None:
        self.source_id = source.id
        self.filename = filename
        self.uuid = str(uuid.uuid4())
        self.size = os.stat(storage.path(source.filesystem_id, filename)).st_size

    def __repr__(self) -> str:
        return "<Submission %r>" % (self.filename)

    @property
    def is_file(self) -> bool:
        return self.filename.endswith("doc.gz.gpg") or self.filename.endswith("doc.zip.gpg")

    @property
    def is_message(self) -> bool:
        return self.filename.endswith("msg.gpg")

    def to_json(self) -> "Dict[str, Any]":
        seen_by = {
            f.journalist.uuid
            for f in SeenFile.query.filter(SeenFile.file_id == self.id)
            if f.journalist
        }
        seen_by.update(
            {
                m.journalist.uuid
                for m in SeenMessage.query.filter(SeenMessage.message_id == self.id)
                if m.journalist
            }
        )
        json_submission = {
            "source_url": url_for("api.single_source", source_uuid=self.source.uuid)
            if self.source
            else None,
            "submission_url": url_for(
                "api.single_submission",
                source_uuid=self.source.uuid,
                submission_uuid=self.uuid,
            )
            if self.source
            else None,
            "filename": self.filename,
            "size": self.size,
            "is_file": self.is_file,
            "is_message": self.is_message,
            "is_read": self.seen,
            "uuid": self.uuid,
            "download_url": url_for(
                "api.download_submission",
                source_uuid=self.source.uuid,
                submission_uuid=self.uuid,
            )
            if self.source
            else None,
            "seen_by": list(seen_by),
        }
        return json_submission

    @property
    def seen(self) -> bool:
        """
        If the submission has been downloaded or seen by any journalist, then the submssion is
        considered seen.
        """
        if self.downloaded or self.seen_files.count() or self.seen_messages.count():
            return True

        return False


class Reply(db.Model):
    __tablename__ = "replies"
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True, nullable=False)

    journalist_id = Column(Integer, ForeignKey("journalists.id"), nullable=False)
    journalist = relationship("Journalist", backref=backref("replies", order_by=id))

    source_id = Column(Integer, ForeignKey("sources.id"))
    source = relationship("Source", backref=backref("replies", order_by=id, cascade="delete"))

    filename = Column(String(255), nullable=False)
    size = Column(Integer, nullable=False)
    """
    The checksum of the encrypted file on disk.
    Format: $hash_name:$hex_encoded_hash_value
    Example: sha256:05fa5efd7d1b608ac1fbdf19a61a5a439d05b05225e81faa63fdd188296b614a
    """
    checksum = Column(String(255))

    deleted_by_source = Column(Boolean, default=False, nullable=False)

    def __init__(
        self, journalist: "Journalist", source: Source, filename: str, storage: Storage
    ) -> None:
        self.journalist = journalist
        self.source_id = source.id
        self.uuid = str(uuid.uuid4())
        self.filename = filename
        self.size = os.stat(storage.path(source.filesystem_id, filename)).st_size

    def __repr__(self) -> str:
        return "<Reply %r>" % (self.filename)

    def to_json(self) -> "Dict[str, Any]":
        seen_by = [r.journalist.uuid for r in SeenReply.query.filter(SeenReply.reply_id == self.id)]
        json_reply = {
            "source_url": url_for("api.single_source", source_uuid=self.source.uuid)
            if self.source
            else None,
            "reply_url": url_for(
                "api.single_reply", source_uuid=self.source.uuid, reply_uuid=self.uuid
            )
            if self.source
            else None,
            "filename": self.filename,
            "size": self.size,
            "journalist_username": self.journalist.username,
            "journalist_first_name": self.journalist.first_name or "",
            "journalist_last_name": self.journalist.last_name or "",
            "journalist_uuid": self.journalist.uuid,
            "uuid": self.uuid,
            "is_deleted_by_source": self.deleted_by_source,
            "seen_by": seen_by,
        }
        return json_reply


class SourceStar(db.Model):
    __tablename__ = "source_stars"
    id = Column("id", Integer, primary_key=True)
    source_id = Column("source_id", Integer, ForeignKey("sources.id"))
    starred = Column("starred", Boolean, default=True)

    def __eq__(self, other: "Any") -> bool:
        if isinstance(other, SourceStar):
            return (
                self.source_id == other.source_id
                and self.id == other.id
                and self.starred == other.starred
            )
        return False

    def __init__(self, source: Source, starred: bool = True) -> None:
        self.source_id = source.id
        self.starred = starred


class InvalidUsernameException(Exception):

    """Raised when a user logs in with an invalid username"""


class FirstOrLastNameError(Exception):
    """Generic error for names that are invalid."""

    def __init__(self, msg: str) -> None:
        super(FirstOrLastNameError, self).__init__(msg)


class InvalidNameLength(FirstOrLastNameError):
    """Raised when attempting to create a Journalist with an invalid name length."""

    def __init__(self) -> None:
        super(InvalidNameLength, self).__init__(gettext("Name too long"))


class LoginThrottledException(Exception):

    """Raised when a user attempts to log in
    too many times in a given time period"""


class WrongPasswordException(Exception):

    """Raised when a user logs in with an incorrect password"""


class BadTokenException(Exception):

    """Raised when a user logins in with an incorrect TOTP token"""


class InvalidOTPSecretException(Exception):

    """Raised when a user's OTP secret is invalid - for example, too short"""


class PasswordError(Exception):

    """Generic error for passwords that are invalid."""


class InvalidPasswordLength(PasswordError):
    """Raised when attempting to create a Journalist or log in with an invalid
    password length.
    """

    def __init__(self, passphrase: str) -> None:
        self.passphrase_len = len(passphrase)

    def __str__(self) -> str:
        if self.passphrase_len > Journalist.MAX_PASSWORD_LEN:
            return "Password is too long."
        if self.passphrase_len < Journalist.MIN_PASSWORD_LEN:
            return "Password is too short."
        return ""  # return empty string that can be appended harmlessly


class NonDicewarePassword(PasswordError):

    """Raised when attempting to validate a password that is not diceware-like"""


class Journalist(db.Model):
    __tablename__ = "journalists"
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True, nullable=False)
    username = Column(String(255), nullable=False, unique=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    pw_salt = Column(LargeBinary(32), nullable=True)
    pw_hash = Column(LargeBinary(256), nullable=True)
    is_admin = Column(Boolean)

    otp_secret = Column(String(32), default=pyotp.random_base32)
    is_totp = Column(Boolean, default=True)
    hotp_counter = Column(Integer, default=0)
    last_token = Column(String(6))

    created_on = Column(DateTime, default=datetime.datetime.utcnow)
    last_access = Column(DateTime)
    passphrase_hash = Column(String(256))

    login_attempts = relationship(
        "JournalistLoginAttempt", backref="journalist", cascade="all, delete"
    )

    MIN_USERNAME_LEN = 3
    MIN_NAME_LEN = 0
    MAX_NAME_LEN = 100
    INVALID_USERNAMES = ["deleted"]

    def __init__(
        self,
        username: str,
        password: str,
        first_name: "Optional[str]" = None,
        last_name: "Optional[str]" = None,
        is_admin: bool = False,
        otp_secret: "Optional[str]" = None,
    ) -> None:

        self.check_username_acceptable(username)
        self.username = username
        if first_name:
            self.check_name_acceptable(first_name)
            self.first_name = first_name
        if last_name:
            self.check_name_acceptable(last_name)
            self.last_name = last_name
        # nosemgrep: python.django.security.audit.unvalidated-password.unvalidated-password
        self.set_password(password)
        self.is_admin = is_admin
        self.uuid = str(uuid.uuid4())

        if otp_secret:
            self.set_hotp_secret(otp_secret)

    def __repr__(self) -> str:
        return "<Journalist {0}{1}>".format(self.username, " [admin]" if self.is_admin else "")

    def _scrypt_hash(self, password: str, salt: bytes) -> bytes:
        backend = default_backend()
        scrypt_instance = scrypt.Scrypt(
            length=64,
            salt=salt,
            n=2**14,
            r=8,
            p=1,
            backend=backend,
        )
        return scrypt_instance.derive(password.encode("utf-8"))

    MAX_PASSWORD_LEN = 128
    MIN_PASSWORD_LEN = 14

    def set_password(self, passphrase: "Optional[str]") -> None:
        if passphrase is None:
            raise PasswordError()

        self.check_password_acceptable(passphrase)

        # "migrate" from the legacy case
        if not self.passphrase_hash:
            self.passphrase_hash = argon2.using(**ARGON2_PARAMS).hash(passphrase)
            # passlib creates one merged field that embeds randomly generated
            # salt in the output like $alg$salt$hash
            self.pw_hash = None
            self.pw_salt = None

        # Don't do anything if user's password hasn't changed.
        if self.passphrase_hash and self.valid_password(passphrase):
            return

        self.passphrase_hash = argon2.using(**ARGON2_PARAMS).hash(passphrase)

    def set_name(self, first_name: Optional[str], last_name: Optional[str]) -> None:
        if first_name:
            self.check_name_acceptable(first_name)
            self.first_name = first_name
        if last_name:
            self.check_name_acceptable(last_name)
            self.last_name = last_name

    @classmethod
    def check_username_acceptable(cls, username: str) -> None:
        if len(username) < cls.MIN_USERNAME_LEN:
            raise InvalidUsernameException(
                ngettext(
                    "Must be at least {num} character long.",
                    "Must be at least {num} characters long.",
                    cls.MIN_USERNAME_LEN,
                ).format(num=cls.MIN_USERNAME_LEN)
            )
        if username in cls.INVALID_USERNAMES:
            raise InvalidUsernameException(
                gettext(
                    "This username is invalid because it is reserved "
                    "for internal use by the software."
                )
            )

    @classmethod
    def check_name_acceptable(cls, name: str) -> None:
        # Enforce a reasonable maximum length for names
        if len(name) > cls.MAX_NAME_LEN:
            raise InvalidNameLength()

    @classmethod
    def check_password_acceptable(cls, password: str) -> None:
        # Enforce a reasonable maximum length for passwords to avoid DoS
        if len(password) > cls.MAX_PASSWORD_LEN:
            raise InvalidPasswordLength(password)

        # Enforce a reasonable minimum length for new passwords
        if len(password) < cls.MIN_PASSWORD_LEN:
            raise InvalidPasswordLength(password)

        # Ensure all passwords are "diceware-like"
        if len(password.split()) < 7:
            raise NonDicewarePassword()

    def valid_password(self, passphrase: "Optional[str]") -> bool:
        if not passphrase:
            return False

        # Avoid hashing passwords that are over the maximum length
        if len(passphrase) > self.MAX_PASSWORD_LEN:
            raise InvalidPasswordLength(passphrase)

        # No check on minimum password length here because some passwords
        # may have been set prior to setting the mininum password length.

        if self.passphrase_hash:
            # default case
            is_valid = argon2.verify(passphrase, self.passphrase_hash)
        else:
            # legacy support
            if self.pw_salt is None:
                raise ValueError(
                    "Should never happen: pw_salt is none for legacy Journalist {}".format(self.id)
                )

            # For type checking
            assert isinstance(self.pw_hash, bytes)

            is_valid = pyotp.utils.compare_digest(
                self._scrypt_hash(passphrase, self.pw_salt), self.pw_hash
            )

        # migrate new passwords
        if is_valid and not self.passphrase_hash:
            self.passphrase_hash = argon2.using(**ARGON2_PARAMS).hash(passphrase)
            # passlib creates one merged field that embeds randomly generated
            # salt in the output like $alg$salt$hash
            self.pw_salt = None
            self.pw_hash = None
            db.session.add(self)
            db.session.commit()

        return is_valid

    def regenerate_totp_shared_secret(self) -> None:
        self.otp_secret = pyotp.random_base32()

    def set_hotp_secret(self, otp_secret: str) -> None:
        self.otp_secret = base64.b32encode(binascii.unhexlify(otp_secret.replace(" ", ""))).decode(
            "ascii"
        )
        self.is_totp = False
        self.hotp_counter = 0

    @property
    def totp(self) -> "TOTP":
        if self.is_totp:
            return pyotp.TOTP(self.otp_secret)
        else:
            raise ValueError("{} is not using TOTP".format(self))

    @property
    def hotp(self) -> "HOTP":
        if not self.is_totp:
            return pyotp.HOTP(self.otp_secret)
        else:
            raise ValueError("{} is not using HOTP".format(self))

    @property
    def shared_secret_qrcode(self) -> Markup:
        uri = self.totp.provisioning_uri(self.username, issuer_name="SecureDrop")

        qr = qrcode.QRCode(box_size=15, image_factory=qrcode.image.svg.SvgPathImage)
        qr.add_data(uri)
        img = qr.make_image()

        svg_out = BytesIO()
        img.save(svg_out)
        return Markup(svg_out.getvalue().decode("utf-8"))

    @property
    def formatted_otp_secret(self) -> str:
        """The OTP secret is easier to read and manually enter if it is all
        lowercase and split into four groups of four characters. The secret is
        base32-encoded, so it is case insensitive."""
        sec = self.otp_secret
        chunks = [sec[i : i + 4] for i in range(0, len(sec), 4)]
        return " ".join(chunks).lower()

    def _format_token(self, token: str) -> str:
        """Strips from authentication tokens the whitespace
        that many clients add for readability"""
        return "".join(token.split())

    def verify_token(self, token: "Optional[str]") -> bool:
        if not token:
            return False

        if self.is_totp:
            # Also check the given token against the previous and next
            # valid tokens, to compensate for potential time skew
            # between the client and the server. The total valid
            # window is 1:30s.
            return self.totp.verify(token, valid_window=1)

        if self.hotp_counter is not None:
            for counter_val in range(self.hotp_counter, self.hotp_counter + 20):
                if self.hotp.verify(token, counter_val):
                    self.hotp_counter = counter_val + 1
                    db.session.commit()
                    return True

        return False

    _LOGIN_ATTEMPT_PERIOD = 60  # seconds
    _MAX_LOGIN_ATTEMPTS_PER_PERIOD = 5

    @classmethod
    def throttle_login(cls, user: "Journalist") -> None:
        # Record the login attempt...
        login_attempt = JournalistLoginAttempt(user)
        db.session.add(login_attempt)
        db.session.commit()

        # ...and reject it if they have exceeded the threshold
        login_attempt_period = datetime.datetime.utcnow() - datetime.timedelta(
            seconds=cls._LOGIN_ATTEMPT_PERIOD
        )
        attempts_within_period = (
            JournalistLoginAttempt.query.filter(JournalistLoginAttempt.journalist_id == user.id)
            .filter(JournalistLoginAttempt.timestamp > login_attempt_period)
            .all()
        )
        if len(attempts_within_period) > cls._MAX_LOGIN_ATTEMPTS_PER_PERIOD:
            raise LoginThrottledException(
                "throttled ({} attempts in last {} seconds)".format(
                    len(attempts_within_period), cls._LOGIN_ATTEMPT_PERIOD
                )
            )

    @classmethod
    def login(
        cls, username: str, password: "Optional[str]", token: "Optional[str]"
    ) -> "Journalist":

        try:
            user = Journalist.query.filter_by(username=username).one()
        except NoResultFound:
            raise InvalidUsernameException(gettext("Invalid username"))

        if user.username in Journalist.INVALID_USERNAMES:
            raise InvalidUsernameException(gettext("Invalid username"))

        if len(user.otp_secret) < OTP_SECRET_MIN_ASCII_LENGTH:
            raise InvalidOTPSecretException(gettext("Invalid OTP secret"))

        # From here to the return the order of statements is very important
        token = user._format_token(token)

        if LOGIN_HARDENING:
            cls.throttle_login(user)

            # Prevent TOTP token reuse
            if user.last_token is not None:
                # For type checking
                assert isinstance(token, str)
                if pyotp.utils.compare_digest(token, user.last_token):
                    raise BadTokenException("previously used two-factor code " "{}".format(token))
        if not user.verify_token(token):
            raise BadTokenException("invalid two-factor code")

        # Store latest token to prevent OTP token reuse
        user.last_token = token
        db.session.commit()

        if not user.valid_password(password):
            raise WrongPasswordException("invalid password")

        return user

    def to_json(self, all_info: bool = True) -> Dict[str, Any]:
        """Returns a JSON representation of the journalist user. If all_info is
        False, potentially sensitive or extraneous fields are excluded. Note
        that both representations do NOT include credentials."""
        json_user = {
            "username": self.username,
            "uuid": self.uuid,
            "first_name": self.first_name,
            "last_name": self.last_name,
        }  # type: Dict[str, Any]

        if all_info is True:
            json_user["is_admin"] = self.is_admin
            if self.last_access:
                json_user["last_login"] = self.last_access
            else:
                json_user["last_login"] = None

        return json_user

    def is_deleted_user(self) -> bool:
        """Is this the special "deleted" user managed by the system?"""
        return self.username == "deleted"

    @classmethod
    def get_deleted(cls) -> "Journalist":
        """Get a system user that represents deleted journalists for referential integrity

        Callers must commit the session themselves
        """
        deleted = Journalist.query.filter_by(username="deleted").one_or_none()
        if deleted is None:
            # Lazily create
            deleted = cls(
                # Use a placeholder username to bypass validation that would reject
                # "deleted" as unusable
                username="placeholder",
                # We store a randomly generated passphrase for this account that is
                # never revealed to anyone.
                password=PassphraseGenerator.get_default().generate_passphrase(),
            )
            deleted.username = "deleted"
            db.session.add(deleted)
        return deleted

    def delete(self) -> None:
        """delete a journalist, migrating some data over to the "deleted" journalist

        Callers must commit the session themselves
        """
        deleted = self.get_deleted()
        # All replies should be reassociated with the "deleted" journalist
        for reply in Reply.query.filter_by(journalist_id=self.id).all():
            reply.journalist_id = deleted.id
            db.session.add(reply)

        # For seen indicators, we need to make sure one doesn't already exist
        # otherwise it'll hit a unique key conflict
        already_seen_files = {
            file.file_id for file in SeenFile.query.filter_by(journalist_id=deleted.id).all()
        }
        for file in SeenFile.query.filter_by(journalist_id=self.id).all():
            if file.file_id in already_seen_files:
                db.session.delete(file)
            else:
                file.journalist_id = deleted.id
                db.session.add(file)

        already_seen_messages = {
            message.message_id
            for message in SeenMessage.query.filter_by(journalist_id=deleted.id).all()
        }
        for message in SeenMessage.query.filter_by(journalist_id=self.id).all():
            if message.message_id in already_seen_messages:
                db.session.delete(message)
            else:
                message.journalist_id = deleted.id
                db.session.add(message)

        already_seen_replies = {
            reply.reply_id for reply in SeenReply.query.filter_by(journalist_id=deleted.id).all()
        }
        for reply in SeenReply.query.filter_by(journalist_id=self.id).all():
            if reply.reply_id in already_seen_replies:
                db.session.delete(reply)
            else:
                reply.journalist_id = deleted.id
                db.session.add(reply)

        # For the rest of the associated data we rely on cascading deletions
        db.session.delete(self)


class SeenFile(db.Model):
    __tablename__ = "seen_files"
    __table_args__ = (db.UniqueConstraint("file_id", "journalist_id"),)
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    journalist_id = Column(Integer, ForeignKey("journalists.id"), nullable=False)
    file = relationship(
        "Submission",
        backref=backref("seen_files", lazy="dynamic", cascade="all,delete"),
    )
    journalist = relationship("Journalist", backref=backref("seen_files"))


class SeenMessage(db.Model):
    __tablename__ = "seen_messages"
    __table_args__ = (db.UniqueConstraint("message_id", "journalist_id"),)
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    journalist_id = Column(Integer, ForeignKey("journalists.id"), nullable=False)
    message = relationship(
        "Submission",
        backref=backref("seen_messages", lazy="dynamic", cascade="all,delete"),
    )
    journalist = relationship("Journalist", backref=backref("seen_messages"))


class SeenReply(db.Model):
    __tablename__ = "seen_replies"
    __table_args__ = (db.UniqueConstraint("reply_id", "journalist_id"),)
    id = Column(Integer, primary_key=True)
    reply_id = Column(Integer, ForeignKey("replies.id"), nullable=False)
    journalist_id = Column(Integer, ForeignKey("journalists.id"), nullable=False)
    reply = relationship("Reply", backref=backref("seen_replies", cascade="all,delete"))
    journalist = relationship("Journalist", backref=backref("seen_replies"))


class JournalistLoginAttempt(db.Model):

    """This model keeps track of journalist's login attempts so we can
    rate limit them in order to prevent attackers from brute forcing
    passwords or two-factor tokens."""

    __tablename__ = "journalist_login_attempt"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    journalist_id = Column(Integer, ForeignKey("journalists.id"), nullable=False)

    def __init__(self, journalist: Journalist) -> None:
        self.journalist = journalist


class InstanceConfig(db.Model):
    """Versioned key-value store of settings configurable from the journalist
    interface.  The current version has valid_until=0 (unix epoch start)
    """

    # Limits length of org name used in SI and JI titles, image alt texts etc.
    MAX_ORG_NAME_LEN = 64

    __tablename__ = "instance_config"
    version = Column(Integer, primary_key=True)
    valid_until = Column(
        DateTime,
        default=datetime.datetime.fromtimestamp(0),
        nullable=False,
        unique=True,
    )
    allow_document_uploads = Column(Boolean, default=True)
    organization_name = Column(String(255), nullable=True, default="SecureDrop")
    initial_message_min_len = Column(Integer, nullable=False, default=0, server_default="0")
    reject_message_with_codename = Column(
        Boolean, nullable=False, default=False, server_default="0"
    )

    # Columns not listed here will be included by InstanceConfig.copy() when
    # updating the configuration.
    metadata_cols = ["version", "valid_until"]

    def __repr__(self) -> str:
        return (
            "<InstanceConfig(version=%s, valid_until=%s, "
            "allow_document_uploads=%s, organization_name=%s, "
            "initial_message_min_len=%s, reject_message_with_codename=%s)>"
            % (
                self.version,
                self.valid_until,
                self.allow_document_uploads,
                self.organization_name,
                self.initial_message_min_len,
                self.reject_message_with_codename,
            )
        )

    def copy(self) -> "InstanceConfig":
        """Make a copy of only the configuration columns of the given
        InstanceConfig object: i.e., excluding metadata_cols.
        """

        new = type(self)()
        for col in self.__table__.columns:
            if col.name in self.metadata_cols:
                continue

            setattr(new, col.name, getattr(self, col.name))

        return new

    @classmethod
    def get_default(cls, refresh: bool = False) -> "InstanceConfig":
        global _default_instance_config
        if (_default_instance_config is None) or (refresh is True):
            _default_instance_config = InstanceConfig.get_current()
        return _default_instance_config

    @classmethod
    def get_current(cls) -> "InstanceConfig":
        """If the database was created via db.create_all(), data migrations
        weren't run, and the "instance_config" table is empty.  In this case,
        save and return a base configuration derived from each setting's
        column-level default.
        """

        try:
            return cls.query.filter(cls.valid_until == datetime.datetime.fromtimestamp(0)).one()
        except NoResultFound:
            try:
                current = cls()
                db.session.add(current)
                db.session.commit()
                return current
            except IntegrityError:
                return cls.query.filter(cls.valid_until == datetime.datetime.fromtimestamp(0)).one()

    @classmethod
    def check_name_acceptable(cls, name: str) -> None:
        # Enforce a reasonable maximum length for names
        if name is None or len(name) == 0:
            raise InvalidNameLength()
        if len(name) > cls.MAX_ORG_NAME_LEN:
            raise InvalidNameLength()

    @classmethod
    def set_organization_name(cls, name: str) -> None:
        """Invalidate the current configuration and append a new one with the
        new organization name.
        """

        old = cls.get_current()
        old.valid_until = datetime.datetime.utcnow()
        db.session.add(old)

        new = old.copy()
        cls.check_name_acceptable(name)
        new.organization_name = name
        db.session.add(new)

        db.session.commit()

    @classmethod
    def update_submission_prefs(
        cls, allow_uploads: bool, min_length: int, reject_codenames: bool
    ) -> None:
        """Invalidate the current configuration and append a new one with the
        updated submission preferences.
        """

        old = cls.get_current()
        old.valid_until = datetime.datetime.utcnow()
        db.session.add(old)

        new = old.copy()
        new.allow_document_uploads = allow_uploads
        new.initial_message_min_len = min_length
        new.reject_message_with_codename = reject_codenames
        db.session.add(new)

        db.session.commit()
