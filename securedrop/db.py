import os
import datetime

# Find the best implementation available on this platform
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Binary
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

import scrypt
import pyotp

import qrcode
# Using svg because it doesn't require additional dependencies
import qrcode.image.svg

import config
import crypto_util
import store

# http://flask.pocoo.org/docs/patterns/sqlalchemy/

if config.DATABASE_ENGINE == "sqlite":
    engine = create_engine(
        config.DATABASE_ENGINE + ":///" +
        config.DATABASE_FILE
    )
else:
    engine = create_engine(
        config.DATABASE_ENGINE + '://' +
        config.DATABASE_USERNAME + ':' +
        config.DATABASE_PASSWORD + '@' +
        config.DATABASE_HOST + '/' +
        config.DATABASE_NAME, echo=False
    )

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def get_one_or_else(query, logger, failure_method):
    try:
        return_value = query.one()
    except MultipleResultsFound as e:
        logger.error("Found multiple while executing %s when one was expected: %s" % (query,e,))
        failure_method(500)
    except NoResultFound as e:
        logger.error("Found none when one was expected: %s" % (e,))
        failure_method(404)
    return return_value


class Source(Base):
    __tablename__ = 'sources'
    id = Column(Integer, primary_key=True)
    filesystem_id = Column(String(96), unique=True)
    journalist_designation = Column(String(255), nullable=False)
    flagged = Column(Boolean, default=False)
    # TODO should we be using utc times?
    last_updated = Column(DateTime, default=datetime.datetime.now)
    star = relationship("SourceStar", uselist=False, backref="source")
    
    # sources are "pending" and don't get displayed to journalists until they submit something
    pending = Column(Boolean, default=True)

    # keep track of how many interactions have happened, for filenames
    interaction_count = Column(Integer, default=0, nullable=False)

    def __init__(self, filesystem_id=None, journalist_designation=None):
        self.filesystem_id = filesystem_id
        self.journalist_designation = journalist_designation

    def __repr__(self):
        return '<Source %r>' % (self.journalist_designation)

    def journalist_filename(self):
        valid_chars = 'abcdefghijklmnopqrstuvwxyz1234567890-_'
        return ''.join([c for c in self.journalist_designation.lower().replace(' ', '_') if c in valid_chars])

    def documents_messages_count(self):
        try:
            return self.docs_msgs_count
        except AttributeError:
            self.docs_msgs_count = {'messages': 0, 'documents': 0}
            for submission in self.submissions:
                if submission.filename.endswith('msg.gpg'):
                    self.docs_msgs_count['messages'] += 1
                elif submission.filename.endswith('doc.zip.gpg'):
                    self.docs_msgs_count['documents'] += 1
            return self.docs_msgs_count


class Submission(Base):
    __tablename__ = 'submissions'
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('sources.id'))
    source = relationship("Source", backref=backref('submissions', order_by=id))
    filename = Column(String(255), nullable=False)
    size = Column(Integer, nullable=False)
    downloaded = Column(Boolean, default=False)

    def __init__(self, source, filename):
        self.source_id = source.id
        self.filename = filename
        self.size = os.stat(store.path(source.filesystem_id, filename)).st_size

    def __repr__(self):
        return '<Submission %r>' % (self.filename)

class SourceStar(Base):
    __tablename__ = 'source_stars'
    id = Column("id", Integer, primary_key=True)
    source_id = Column("source_id", Integer, ForeignKey('sources.id'))
    starred = Column("starred", Boolean, default=True)

    def __eq__(self, other):
        if isinstance(other, SourceStar):
            return self.source_id == other.source_id and self.id == other.id and self.starred == other.starred
        return NotImplemented

    def __init__(self, source, starred=True):
        self.source_id = source.id
        self.starred = starred


class WrongPasswordException(Exception):
    pass


class Journalist(Base):
    __tablename__ = "journalists"
    id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False, unique=True)
    pw_salt = Column(Binary(32))
    pw_hash = Column(Binary(256))
    is_admin = Column(Boolean)
    otp_secret = Column(String(16), default=pyotp.random_base32)

    # TODO should we be using utc times?
    created_on = Column(DateTime, default=datetime.datetime.now)
    last_access = Column(DateTime)

    def __init__(self, username, password, is_admin=False):
        self.username = username
        self.set_password(password)
        self.is_admin = is_admin

    def __repr__(self):
        return "<Journalist {0}{1}>".format(self.username,
                                            " [admin]" if self.is_admin else "")

    def _gen_salt(self, salt_bytes=32):
        return os.urandom(salt_bytes)

    _SCRYPT_PARAMS = dict(N=2**14, r=8, p=1)
    def _scrypt_hash(self, password, salt, params=None):
        if not params:
            params = self._SCRYPT_PARAMS
        # TODO: better handle encoding?
        return scrypt.hash(str(password), salt, **params)

    def set_password(self, password):
        self.pw_salt = self._gen_salt()
        self.pw_hash = self._scrypt_hash(password, self.pw_salt)

    def valid_password(self, password):
        return self._scrypt_hash(password, self.pw_salt) == self.pw_hash

    @property
    def totp(self):
        return pyotp.TOTP(self.otp_secret)

    @property
    def shared_secret_qrcode(self):
        uri = self.totp.provisioning_uri("{}@{}".format(self.username,
                                                        "SecureDrop"))

        qr = qrcode.QRCode(
            box_size=25,
            image_factory=qrcode.image.svg.SvgPathImage
        )
        qr.add_data(uri)
        img = qr.make_image()

        svg_out = StringIO()
        img.save(svg_out)
        return svg_out.getvalue()

    @property
    def formatted_otp_secret(self):
        """The OTP secret is easier to read and manually enter if it is all
        lowercase and split into four groups of four characters. The secret is
        base32-encoded, so it is case insensitive."""
        sec = self.otp_secret
        chunks = [ sec[i:i+4] for i in xrange(0, len(sec), 4) ]
        return ' '.join(chunks).lower()

    @staticmethod
    def login(username, password):
        user = Journalist.query.filter_by(username=username).one()
        if not user.valid_password(password):
            raise WrongPasswordException
        return user

# Declare (or import) models before init_db
def init_db():
    Base.metadata.create_all(bind=engine)

