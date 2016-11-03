# -*- coding: utf-8 -*-
import cPickle as pickle
from flask.helpers import total_seconds
from flask.sessions import SessionInterface as FlaskSessionInterface
from flask.sessions import SessionMixin
import redis
import uuid
from werkzeug.datastructures import CallbackDict

from crypto_util import AES_then_HMAC, BadSignature

# The SecureDrop application server is rebooted every 24 hours to ensure all
# sensitive data is wiped from memory (see
# https://github.com/freedomofpress/securedrop/pull/805). We generate ephemeral
# encryption and authentication keys that last until reboot so we can secure
# cookie data in a way that provides forward deniability in the case that a
# a cookie is later retrieved.

class Session:
    def __init__(self, app):
        config = app.config.copy()
        config.setdefault('SESSION_TIMEOUT', 60 * 60 * 24)
        config.setdefault('SESSION_COOKIE_SECURE', False)
        ephemeral_keys_str = AES_then_HMAC.gen_keys_string()
        app.session_interface = SDSessionInterface(config['SESSION_TIMEOUT'],
                                                   config['SESSION_COOKIE_SECURE'],
                                                   ephemeral_keys_str)


class SDSession(CallbackDict, SessionMixin):
    """The SecureDrop session class exposes a dict-like interface, which
    is intended to function as a drop-in replacement for the default
    Flask session object. While it holds the Redis session identifier,
    which is used to manage session expiry, this is not indended to be
    worked with directly and is stored as an attribute."""

    def __init__(self, uuid, initial=None):
        def on_update(self):
            self.modified = True
        self.uuid = uuid
        if initial:
            super(SDSession, self).__init__(initial, on_update)
        self.modified = False


class SDSessionInterface(FlaskSessionInterface):
    """The SD session interface implements an authentication scheme that
    minimizes the time the source codename spends in server memory,
    encrypts and signs the client-side session with an ephemeral key to
    provide forward-deniability of cookie authenticity, and implements a
    server-side session expiration method based on a timeout.
    
    :param int session_timeout: The time in seconds of inactivity before
                                expiring a session.
    """
    serializer = pickle
    session_class = SDSession
    redis = redis.StrictRedis() 
    aenc = AES_then_HMAC.encrypt_then_mac
    adec = AES_then_HMAC.authenticate_then_decrypt

    def __init__(self, session_timeout, secure, ephemeral_keys_str):
        self.session_timeout = session_timeout
        self.secure = secure
        self.ephemeral_keys_str = ephemeral_keys_str

    def _generate_uuid(self):
        """Generate the pseudo-random variant of the Universally Unique
        IDentifier (RFC 4122). Returns an :obj:`str`.
        """
        return str(uuid.uuid4())

    def open_session(self, app, request):
        # Make sure our ephemeral key exists and complies with spec
        if not AES_then_HMAC.extract_keys(self.ephemeral_keys_str):
            return None

        # First check the cookie data exists
        cookie_data = request.cookies.get(app.session_cookie_name)
        if not cookie_data:
            return self.session_class(self._generate_uuid())

        # Next, check the authentication. If the signature is valid, then
        # decrypt and deserialize.
        try:
            client_data_string = self.adec(self.ephemeral_keys_str,
                                           cookie_data)
        except BadSignature:
            1/0
            return self.session_class(self._generate_uuid())
        client_data = self.serializer.loads(client_data_string)

        # Last, make sure the session has not expired.
        uuid = client_data.pop("uuid")
        session_valid = self.redis.get(self.app.session_cookie_name + uuid)
        if not bool(session_valid):
            return self.session_class(self._generate_uuid())
        return self.session_class(uuid, client_data)


    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        # Delete case. If there is no session we bail early. If the session was
        # modified to be empty we remove the whole cookie, and the uuid key
        # from the key-val store.
        if not session:
            if session.modified:
                response.delete_cookie(app.session_cookie_name, domain=domain)
                self.redis.delete(self.key_prefix + session.sid)
            return

        # Reset the session timeout each time we see activity.
        self.redis.psetex(app.session_cookie_name + session.uuid,
                          self.session_timeout, "True")

        # Set a cookie if the session has been modified.
        if True:
            client_session = dict(session)
            client_session.update(uuid=session.uuid)
            client_session_string = self.serializer.dumps(client_session)
            cookie_val = self.aenc(self.ephemeral_keys_str,
                                   client_session_string)
            response.set_cookie(app.session_cookie_name, cookie_val,
                                httponly=True, domain=domain,
                                secure=self.secure)
