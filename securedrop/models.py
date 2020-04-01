# -*- coding: utf-8 -*-
import binascii
import datetime
import base64
import os
import scrypt
import pyotp
import qrcode
# Using svg because it doesn't require additional dependencies
import qrcode.image.svg
import uuid
from io import BytesIO

from flask import current_app, url_for
from itsdangerous import TimedJSONWebSignatureSerializer, BadData
from jinja2 import Markup
from passlib.hash import argon2
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Column, Integer, String, Boolean, DateTime, LargeBinary
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from db import db

import typing

if typing.TYPE_CHECKING:
    # flake8 can not understand type annotation yet.
    # That is why all type annotation relative import
    # statements has to be marked as noqa.
    # http://flake8.pycqa.org/en/latest/user/error-codes.html?highlight=f401
    from typing import Callable, Optional, Union, Dict, List, Any  # noqa: F401
    from io import BufferedIOBase  # noqa: F401
    from logging import Logger  # noqa: F401
    from sqlalchemy import Query  # noqa: F401
    from pyotp import OTP  # noqa: F401

LOGIN_HARDENING = True
if os.environ.get('SECUREDROP_ENV') == 'test':
    LOGIN_HARDENING = False

ARGON2_PARAMS = dict(memory_cost=2**16, rounds=4, parallelism=2)


def get_one_or_else(query, logger, failure_method):
    # type: (Query, Logger, Callable[[int], None]) -> None
    try:
        return query.one()
    except MultipleResultsFound as e:
        logger.error(
            "Found multiple while executing %s when one was expected: %s" %
            (query, e, ))
        failure_method(500)
    except NoResultFound as e:
        logger.error("Found none when one was expected: %s" % (e,))
        failure_method(404)


class Source(db.Model):
    __tablename__ = 'sources'
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True, nullable=False)
    filesystem_id = Column(String(96), unique=True)
    journalist_designation = Column(String(255), nullable=False)
    flagged = Column(Boolean, default=False)
    last_updated = Column(DateTime)
    star = relationship("SourceStar", uselist=False, backref="source")

    # sources are "pending" and don't get displayed to journalists until they
    # submit something
    pending = Column(Boolean, default=True)

    # keep track of how many interactions have happened, for filenames
    interaction_count = Column(Integer, default=0, nullable=False)

    # Don't create or bother checking excessively long codenames to prevent DoS
    NUM_WORDS = 7
    MAX_CODENAME_LEN = 128

    def __init__(self, filesystem_id=None, journalist_designation=None):
        # type: (str, str) -> None
        self.filesystem_id = filesystem_id
        self.journalist_designation = journalist_designation
        self.uuid = str(uuid.uuid4())

    def __repr__(self):
        # type: () -> str
        return '<Source %r>' % (self.journalist_designation)

    @property
    def journalist_filename(self):
        # type: () -> str
        valid_chars = 'abcdefghijklmnopqrstuvwxyz1234567890-_'
        return ''.join([c for c in self.journalist_designation.lower().replace(
            ' ', '_') if c in valid_chars])

    def documents_messages_count(self):
        # type: () -> Dict[str, int]
        self.docs_msgs_count = {'messages': 0, 'documents': 0}
        for submission in self.submissions:
            if submission.filename.endswith('msg.gpg'):
                self.docs_msgs_count['messages'] += 1
            elif (submission.filename.endswith('doc.gz.gpg') or
                  submission.filename.endswith('doc.zip.gpg')):
                self.docs_msgs_count['documents'] += 1
        return self.docs_msgs_count

    @property
    def collection(self):
        # type: () -> List[Union[Submission, Reply]]
        """Return the list of submissions and replies for this source, sorted
        in ascending order by the filename/interaction count."""
        collection = []  # type: List[Union[Submission, Reply]]
        collection.extend(self.submissions)
        collection.extend(self.replies)
        collection.sort(key=lambda x: int(x.filename.split('-')[0]))
        return collection

    @property
    def fingerprint(self):
        return current_app.crypto_util.get_fingerprint(self.filesystem_id)

    @fingerprint.setter
    def fingerprint(self, value):
        raise NotImplementedError

    @fingerprint.deleter
    def fingerprint(self):
        raise NotImplementedError

    @property
    def public_key(self):
        # type: () -> str
        return current_app.crypto_util.get_pubkey(self.filesystem_id)

    @public_key.setter
    def public_key(self, value):
        # type: (str) -> None
        raise NotImplementedError

    @public_key.deleter
    def public_key(self):
        # type: () -> None
        raise NotImplementedError

    def to_json(self):
        # type: () -> Dict[str, Union[str, bool, int, str]]
        docs_msg_count = self.documents_messages_count()

        if self.last_updated:
            last_updated = self.last_updated.isoformat() + 'Z'
        else:
            last_updated = datetime.datetime.utcnow().isoformat() + 'Z'

        if self.star and self.star.starred:
            starred = True
        else:
            starred = False

        json_source = {
            'uuid': self.uuid,
            'url': url_for('api.single_source', source_uuid=self.uuid),
            'journalist_designation': self.journalist_designation,
            'is_flagged': self.flagged,
            'is_starred': starred,
            'last_updated': last_updated,
            'interaction_count': self.interaction_count,
            'key': {
              'type': 'PGP',
              'public': self.public_key,
              'fingerprint': self.fingerprint
            },
            'number_of_documents': docs_msg_count['documents'],
            'number_of_messages': docs_msg_count['messages'],
            'submissions_url': url_for('api.all_source_submissions',
                                       source_uuid=self.uuid),
            'add_star_url': url_for('api.add_star', source_uuid=self.uuid),
            'remove_star_url': url_for('api.remove_star',
                                       source_uuid=self.uuid),
            'replies_url': url_for('api.all_source_replies',
                                   source_uuid=self.uuid)
            }
        return json_source


class Submission(db.Model):
    __tablename__ = 'submissions'
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True, nullable=False)
    source_id = Column(Integer, ForeignKey('sources.id'))
    source = relationship(
        "Source",
        backref=backref("submissions", order_by=id, cascade="delete")
        )

    filename = Column(String(255), nullable=False)
    size = Column(Integer, nullable=False)
    downloaded = Column(Boolean, default=False)
    '''
    The checksum of the encrypted file on disk.
    Format: $hash_name:$hex_encoded_hash_value
    Example: sha256:05fa5efd7d1b608ac1fbdf19a61a5a439d05b05225e81faa63fdd188296b614a
    '''
    checksum = Column(String(255))

    def __init__(self, source, filename):
        # type: (Source, str) -> None
        self.source_id = source.id
        self.filename = filename
        self.uuid = str(uuid.uuid4())
        self.size = os.stat(current_app.storage.path(source.filesystem_id,
                                                     filename)).st_size

    def __repr__(self):
        # type: () -> str
        return '<Submission %r>' % (self.filename)

    def to_json(self):
        # type: () -> Dict[str, Union[str, int, bool]]
        json_submission = {
            'source_url': url_for('api.single_source',
                                  source_uuid=self.source.uuid),
            'submission_url': url_for('api.single_submission',
                                      source_uuid=self.source.uuid,
                                      submission_uuid=self.uuid),
            'filename': self.filename,
            'size': self.size,
            'is_read': self.downloaded,
            'uuid': self.uuid,
            'download_url': url_for('api.download_submission',
                                    source_uuid=self.source.uuid,
                                    submission_uuid=self.uuid),
        }
        return json_submission


class Reply(db.Model):
    __tablename__ = "replies"
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True, nullable=False)

    journalist_id = Column(Integer, ForeignKey('journalists.id'))
    journalist = relationship(
        "Journalist",
        backref=backref(
            'replies',
            order_by=id))

    source_id = Column(Integer, ForeignKey('sources.id'))
    source = relationship(
        "Source",
        backref=backref("replies", order_by=id, cascade="delete")
        )

    filename = Column(String(255), nullable=False)
    size = Column(Integer, nullable=False)
    '''
    The checksum of the encrypted file on disk.
    Format: $hash_name:$hex_encoded_hash_value
    Example: sha256:05fa5efd7d1b608ac1fbdf19a61a5a439d05b05225e81faa63fdd188296b614a
    '''
    checksum = Column(String(255))

    deleted_by_source = Column(Boolean, default=False, nullable=False)

    def __init__(self, journalist, source, filename):
        # type: (Journalist, Source, str) -> None
        self.journalist_id = journalist.id
        self.source_id = source.id
        self.uuid = str(uuid.uuid4())
        self.filename = filename
        self.size = os.stat(current_app.storage.path(source.filesystem_id,
                                                     filename)).st_size

    def __repr__(self):
        # type: () -> str
        return '<Reply %r>' % (self.filename)

    def to_json(self):
        # type: () -> Dict[str, Union[str, int, bool]]
        username = "deleted"
        first_name = ""
        last_name = ""
        uuid = "deleted"
        if self.journalist:
            username = self.journalist.username
            first_name = self.journalist.first_name
            last_name = self.journalist.last_name
            uuid = self.journalist.uuid
        json_submission = {
            'source_url': url_for('api.single_source',
                                  source_uuid=self.source.uuid),
            'reply_url': url_for('api.single_reply',
                                 source_uuid=self.source.uuid,
                                 reply_uuid=self.uuid),
            'filename': self.filename,
            'size': self.size,
            'journalist_username': username,
            'journalist_first_name': first_name,
            'journalist_last_name': last_name,
            'journalist_uuid': uuid,
            'uuid': self.uuid,
            'is_deleted_by_source': self.deleted_by_source,
        }
        return json_submission


class SourceStar(db.Model):
    __tablename__ = 'source_stars'
    id = Column("id", Integer, primary_key=True)
    source_id = Column("source_id", Integer, ForeignKey('sources.id'))
    starred = Column("starred", Boolean, default=True)

    def __eq__(self, other):
        # type: (Any) -> bool
        if isinstance(other, SourceStar):
            return (self.source_id == other.source_id and
                    self.id == other.id and self.starred == other.starred)
        return False

    def __init__(self, source, starred=True):
        # type: (Source, bool) -> None
        self.source_id = source.id
        self.starred = starred


class InvalidUsernameException(Exception):

    """Raised when a user logs in with an invalid username"""


class FirstOrLastNameError(Exception):
    """Generic error for names that are invalid."""

    def __init__(self, msg):
        msg = 'Invalid first or last name.'
        super(FirstOrLastNameError, self).__init__(msg)


class InvalidNameLength(FirstOrLastNameError):
    """Raised when attempting to create a Journalist with an invalid name length."""

    def __init__(self, name):
        self.name_len = len(name)
        if self.name_len > Journalist.MAX_NAME_LEN:
            msg = "Name too long (len={})".format(self.name_len)
        super(InvalidNameLength, self).__init__(msg)


class LoginThrottledException(Exception):

    """Raised when a user attempts to log in
    too many times in a given time period"""


class WrongPasswordException(Exception):

    """Raised when a user logs in with an incorrect password"""


class BadTokenException(Exception):

    """Raised when a user logins in with an incorrect TOTP token"""


class PasswordError(Exception):

    """Generic error for passwords that are invalid.
    """


class InvalidPasswordLength(PasswordError):
    """Raised when attempting to create a Journalist or log in with an invalid
       password length.
    """

    def __init__(self, passphrase):
        # type: (str) -> None
        self.passphrase_len = len(passphrase)

    def __str__(self):
        # type: () -> str
        if self.passphrase_len > Journalist.MAX_PASSWORD_LEN:
            return "Password too long (len={})".format(self.passphrase_len)
        if self.passphrase_len < Journalist.MIN_PASSWORD_LEN:
            return "Password needs to be at least {} characters".format(
                Journalist.MIN_PASSWORD_LEN
            )
        return ""   # return empty string that can be appended harmlessly


class NonDicewarePassword(PasswordError):

    """Raised when attempting to validate a password that is not diceware-like
    """


class Journalist(db.Model):
    __tablename__ = "journalists"
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True, nullable=False)
    username = Column(String(255), nullable=False, unique=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    pw_salt = Column(LargeBinary(32))
    pw_hash = Column(LargeBinary(256))
    is_admin = Column(Boolean)
    session_nonce = Column(Integer, nullable=False, default=0)

    otp_secret = Column(String(16), default=pyotp.random_base32)
    is_totp = Column(Boolean, default=True)
    hotp_counter = Column(Integer, default=0)
    last_token = Column(String(6))

    created_on = Column(DateTime, default=datetime.datetime.utcnow)
    last_access = Column(DateTime)
    passphrase_hash = Column(String(256))
    login_attempts = relationship(
        "JournalistLoginAttempt",
        backref="journalist")

    MIN_USERNAME_LEN = 3
    MIN_NAME_LEN = 0
    MAX_NAME_LEN = 100

    def __init__(self, username, password, first_name=None, last_name=None, is_admin=False,
                 otp_secret=None):
        # type: (str, str, Optional[str], Optional[str], bool, Optional[str]) -> None

        self.check_username_acceptable(username)
        self.username = username
        if first_name:
            self.check_name_acceptable(first_name)
        self.first_name = first_name
        if last_name:
            self.check_name_acceptable(last_name)
        self.last_name = last_name
        self.set_password(password)
        self.is_admin = is_admin
        self.uuid = str(uuid.uuid4())

        if otp_secret:
            self.set_hotp_secret(otp_secret)

    def __repr__(self):
        # type: () -> str
        return "<Journalist {0}{1}>".format(
            self.username,
            " [admin]" if self.is_admin else "")

    _LEGACY_SCRYPT_PARAMS = dict(N=2**14, r=8, p=1)

    def _scrypt_hash(self, password, salt):
        # type: (str, str) -> str
        return scrypt.hash(str(password), salt, **self._LEGACY_SCRYPT_PARAMS)

    MAX_PASSWORD_LEN = 128
    MIN_PASSWORD_LEN = 14

    def set_password(self, passphrase):
        # type: (str) -> None
        self.check_password_acceptable(passphrase)

        # "migrate" from the legacy case
        if not self.passphrase_hash:
            self.passphrase_hash = \
                argon2.using(**ARGON2_PARAMS).hash(passphrase)
            # passlib creates one merged field that embeds randomly generated
            # salt in the output like $alg$salt$hash
            self.pw_hash = None
            self.pw_salt = None

        # Don't do anything if user's password hasn't changed.
        if self.passphrase_hash and self.valid_password(passphrase):
            return

        self.passphrase_hash = argon2.using(**ARGON2_PARAMS).hash(passphrase)

    def set_name(self, first_name, last_name):
        if first_name:
            self.check_name_acceptable(first_name)
        if last_name:
            self.check_name_acceptable(last_name)
        self.first_name = first_name
        self.last_name = last_name

    @classmethod
    def check_username_acceptable(cls, username):
        # type: (str) -> None
        if len(username) < cls.MIN_USERNAME_LEN:
            raise InvalidUsernameException(
                        'Username "{}" must be at least {} characters long.'
                        .format(username, cls.MIN_USERNAME_LEN))

    @classmethod
    def check_name_acceptable(cls, name):
        # Enforce a reasonable maximum length for names
        if len(name) > cls.MAX_NAME_LEN:
            raise InvalidNameLength(name)

    @classmethod
    def check_password_acceptable(cls, password):
        # type: (str) -> None
        # Enforce a reasonable maximum length for passwords to avoid DoS
        if len(password) > cls.MAX_PASSWORD_LEN:
            raise InvalidPasswordLength(password)

        # Enforce a reasonable minimum length for new passwords
        if len(password) < cls.MIN_PASSWORD_LEN:
            raise InvalidPasswordLength(password)

        # Ensure all passwords are "diceware-like"
        if len(password.split()) < 7:
            raise NonDicewarePassword()

    def valid_password(self, passphrase):
        # type: (str) -> bool
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
            is_valid = pyotp.utils.compare_digest(
                self._scrypt_hash(passphrase, self.pw_salt),
                self.pw_hash)

        # migrate new passwords
        if is_valid and not self.passphrase_hash:
            self.passphrase_hash = \
                argon2.using(**ARGON2_PARAMS).hash(passphrase)
            # passlib creates one merged field that embeds randomly generated
            # salt in the output like $alg$salt$hash
            self.pw_salt = None
            self.pw_hash = None
            db.session.add(self)
            db.session.commit()

        return is_valid

    def regenerate_totp_shared_secret(self):
        # type: () -> None
        self.otp_secret = pyotp.random_base32()

    def set_hotp_secret(self, otp_secret):
        # type: (str) -> None
        self.otp_secret = base64.b32encode(
            binascii.unhexlify(
                otp_secret.replace(
                    " ",
                    "")))
        self.is_totp = False
        self.hotp_counter = 0

    @property
    def totp(self):
        # type: () -> OTP
        if self.is_totp:
            return pyotp.TOTP(self.otp_secret)
        else:
            raise ValueError('{} is not using TOTP'.format(self))

    @property
    def hotp(self):
        # type: () -> OTP
        if not self.is_totp:
            return pyotp.HOTP(self.otp_secret)
        else:
            raise ValueError('{} is not using HOTP'.format(self))

    @property
    def shared_secret_qrcode(self):
        # type: () -> Markup
        uri = self.totp.provisioning_uri(
            self.username,
            issuer_name="SecureDrop")

        qr = qrcode.QRCode(
            box_size=15,
            image_factory=qrcode.image.svg.SvgPathImage
        )
        qr.add_data(uri)
        img = qr.make_image()

        svg_out = BytesIO()
        img.save(svg_out)
        return Markup(svg_out.getvalue().decode('utf-8'))

    @property
    def formatted_otp_secret(self):
        # type: () -> str
        """The OTP secret is easier to read and manually enter if it is all
        lowercase and split into four groups of four characters. The secret is
        base32-encoded, so it is case insensitive."""
        sec = self.otp_secret
        chunks = [sec[i:i + 4] for i in range(0, len(sec), 4)]
        return ' '.join(chunks).lower()

    def _format_token(self, token):
        # type: (str) -> str
        """Strips from authentication tokens the whitespace
        that many clients add for readability"""
        return ''.join(token.split())

    def verify_token(self, token):
        # type: (str) -> bool
        token = self._format_token(token)

        # Store latest token to prevent OTP token reuse
        self.last_token = token
        db.session.commit()

        if self.is_totp:
            # Also check the given token against the previous and next
            # valid tokens, to compensate for potential time skew
            # between the client and the server. The total valid
            # window is 1:30s.
            return self.totp.verify(token, valid_window=1)
        else:
            for counter_val in range(
                    self.hotp_counter,
                    self.hotp_counter + 20):
                if self.hotp.verify(token, counter_val):
                    self.hotp_counter = counter_val + 1
                    db.session.commit()
                    return True
            return False

    _LOGIN_ATTEMPT_PERIOD = 60  # seconds
    _MAX_LOGIN_ATTEMPTS_PER_PERIOD = 5

    @classmethod
    def throttle_login(cls, user):
        # type: (Journalist) -> None
        # Record the login attempt...
        login_attempt = JournalistLoginAttempt(user)
        db.session.add(login_attempt)
        db.session.commit()

        # ...and reject it if they have exceeded the threshold
        login_attempt_period = datetime.datetime.utcnow() - \
            datetime.timedelta(seconds=cls._LOGIN_ATTEMPT_PERIOD)
        attempts_within_period = JournalistLoginAttempt.query.filter(
            JournalistLoginAttempt.journalist_id == user.id).filter(
            JournalistLoginAttempt.timestamp > login_attempt_period).all()
        if len(attempts_within_period) > cls._MAX_LOGIN_ATTEMPTS_PER_PERIOD:
            raise LoginThrottledException(
                "throttled ({} attempts in last {} seconds)".format(
                    len(attempts_within_period),
                    cls._LOGIN_ATTEMPT_PERIOD))

    @classmethod
    def login(cls, username, password, token):
        # type: (str, str, str) -> Journalist
        try:
            user = Journalist.query.filter_by(username=username).one()
        except NoResultFound:
            raise InvalidUsernameException(
                "invalid username '{}'".format(username))

        if LOGIN_HARDENING:
            cls.throttle_login(user)

            # Prevent TOTP token reuse
            if user.last_token is not None:
                if pyotp.utils.compare_digest(token, user.last_token):
                    raise BadTokenException("previously used two-factor code "
                                            "{}".format(token))
        if not user.verify_token(token):
            raise BadTokenException("invalid two-factor code")
        if not user.valid_password(password):
            raise WrongPasswordException("invalid password")
        return user

    def generate_api_token(self, expiration):
        # type: (int) -> str
        s = TimedJSONWebSignatureSerializer(
            current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id}).decode('ascii')  # type:ignore

    @staticmethod
    def validate_token_is_not_expired_or_invalid(token):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            s.loads(token)
        except BadData:
            return None

        return True

    @staticmethod
    def validate_api_token_and_get_user(token):
        # type: (str) -> Union[Journalist, None]
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except BadData:
            return None

        revoked_token = RevokedToken.query.filter_by(token=token).one_or_none()
        if revoked_token is not None:
            return None

        return Journalist.query.get(data['id'])

    def to_json(self):
        # type: () -> Dict[str, Union[str, bool, str]]
        json_user = {
            'username': self.username,
            'last_login': self.last_access.isoformat() + 'Z',
            'is_admin': self.is_admin,
            'uuid': self.uuid,
            'first_name': self.first_name,
            'last_name': self.last_name
        }
        return json_user


class JournalistLoginAttempt(db.Model):

    """This model keeps track of journalist's login attempts so we can
    rate limit them in order to prevent attackers from brute forcing
    passwords or two-factor tokens."""
    __tablename__ = "journalist_login_attempt"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    journalist_id = Column(Integer, ForeignKey('journalists.id'))

    def __init__(self, journalist):
        # type: (Journalist) -> None
        self.journalist_id = journalist.id


class RevokedToken(db.Model):

    """
    API tokens that have been revoked either through a logout or other revocation mechanism.
    """

    __tablename__ = 'revoked_tokens'

    id = Column(Integer, primary_key=True)
    journalist_id = Column(Integer, ForeignKey('journalists.id'))
    token = db.Column(db.Text, nullable=False, unique=True)


class InstanceConfig(db.Model):
    '''Versioned key-value store of settings configurable from the journalist
    interface.  The current version has valid_until=None.
    '''

    __tablename__ = 'instance_config'
    version = Column(Integer, primary_key=True)
    valid_until = Column(DateTime, default=None, unique=True)

    allow_document_uploads = Column(Boolean, default=True)

    # Columns not listed here will be included by InstanceConfig.copy() when
    # updating the configuration.
    metadata_cols = ['version', 'valid_until']

    def __repr__(self):
        return "<InstanceConfig(version=%s, valid_until=%s)>" % (self.version, self.valid_until)

    def copy(self):
        '''Make a copy of only the configuration columns of the given
        InstanceConfig object: i.e., excluding metadata_cols.
        '''

        new = type(self)()
        for col in self.__table__.columns:
            if col.name in self.metadata_cols:
                continue

            setattr(new, col.name, getattr(self, col.name))

        return new

    @classmethod
    def get_current(cls):
        '''If the database was created via db.create_all(), data migrations
        weren't run, and the "instance_config" table is empty.  In this case,
        save and return a base configuration derived from each setting's
        column-level default.
        '''

        try:
            return cls.query.filter(cls.valid_until == None).one()  # lgtm [py/test-equals-none]  # noqa: E711, E501
        except NoResultFound:
            current = cls()
            db.session.add(current)
            db.session.commit()
            return current

    @classmethod
    def set(cls, name, value):
        '''Invalidate the current configuration and append a new one with the
        requested change.
        '''

        old = cls.get_current()
        old.valid_until = datetime.datetime.utcnow()
        db.session.add(old)

        new = old.copy()
        setattr(new, name, value)
        db.session.add(new)

        db.session.commit()
