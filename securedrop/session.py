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
EPHEMERAL_KEYS_STR = AES_then_HMAC.gen_keys_string()

class Session:
    def __init__(self, app):
        app.session_interface = self._get_interface(app)

    def _get_interface(self, app):
        config = app.config.copy()
        config.setdefault('SESSION_TIMEOUT', 60 * 60 * 24)
        return SDSessionInterface(config['SESSION_TIMEOUT'])


class SDSession(CallbackDict, SessionMixin):
    """The SecureDrop session class exposes a dict-like interface, which
    is intended to function as a drop-in replacement for the default
    Flask session object. While it holds the Redis session identifier,
    which is used to manage session expiry, this is not indended to be
    worked with directly and is stored as an attribute."""

    def __init__(self, uuid=None, codename=None):
        def on_update(self):
            self.modified = True
        assert sid, "Session UUID missing!"
        session.uuid = uuid
        initial = dict(uuid=uuid, codename=codename)
        if codename:
            super(SDSession, self).__init__(initial=initial,
                                            on_update=on_update)
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

    def __init__(self, session_timeout):
        self.session_lifetime = session_timeout

    def _generate_uuid(self):
        """Generate the pseudo-random variant of the Universally Unique
        IDentifier (RFC 4122). Returns an :obj:`str`.
        """
        return str(uuid.uuid4())

    def open_session(self, app, request):
        # Make sure our ephemeral key exists and complies with spec
        if not AES_then_HMAC.extract_keys(EPHEMERAL_KEYS_STR):
            return None

        # First check the cookie data exists
        cookie_data = request.cookies.get(app.session_cookie_name)
        if not cookie_data:
            return self.session_class(uuid=self._generate_uuid())
        # Next, check the authentication. If the signature is valid, then
        # decrypt and deserialize.
        try:
            client_data = serializer.loads(
                AES_then_HMAC.authenticate_then_decrypt(EPHEMERAL_KEYS_STR,
                                                        cookie_data))
        except BadSignature:
            return self.session_class(uuid=self._generate_uuid())
        # Last, make sure the session has not expired.
        session_valid = self.redis.get(self.app.session_cookie_name +
                                       client_data["uuid"])
        if not bool(session_valid):
            return self.session_class(uuid=self._generate_uuid())

        return self.session_class(**client_data)


    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        # Delete case.  If there is no session we bail early.
        # If the session was modified to be empty we remove the
        # whole cookie.
        if not session:
            if session.modified:
                response.delete_cookie(app.session_cookie_name, domain=domain)
            if self.redis.get(self.app.session_cookie_name +
                                       client_data["uuid"])

            return

        # Reset the session timeout each time we see activity.
        self.redis.psetex(app.session_cookie_name + session["uuid"],
                          total_seconds(self.session_timeout), "True")
        # Set a cookie with the client-side data if it's changed.
        if session.modified:
        client_side_session = AES_then_HMAC(EPHEMERAL_KEYS_STR,
                                            serializer.dumps(**dict(session)))
        response.set_cookie(app.session_cookie_name, value=client_side_session,
                            httponly=True, domain=domain,
                            secure=secure)
