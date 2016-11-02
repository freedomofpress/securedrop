# -*- coding: utf-8 -*-
import cPickle as pickle
from Crypto.Cipher import AES
from Crypto.Util import Counter
from flask.helpers import total_seconds
from flask.sessions import SessionInterface as FlaskSessionInterface
from flask.sessions import SessionMixin
import hashlib
import hmac
import os
from redis import Redis
import scrypt
from uuid import uuid4
from werkzeug.datastructures import CallbackDict

from crypto_util import AES_then_HMAC

class Session:
    def __init__(self, app):
        app.session_interface = self._get_interface(app)

    def _get_interface(self, app):
        config = app.config.copy()
        config.setdefault('SESSION_REDIS', None)
        config.setdefault('REDIS_SESSION_LIFETIME', None)
        return RedisSessionInterface(config['SESSION_REDIS'],
                                     config['REDIS_SESSION_LIFETIME'])


class RedisSession(CallbackDict, SessionMixin):
    """Base class for all SecureDrop sessions."""

    def __init__(self, initial=None, sid=None, key=None, permanent=None):
        def on_update(self):
            self.modified = True
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.key = key
        if permanent:
            self.permanent = permanent
        self.modified = False


class SessionInterface(FlaskSessionInterface):

    def _generate_sid_and_keys_string(self):
        sid = str(uuid4())
        keys_string = AES_then_HMAC.gen_keys_string()
        return sid, keys_string


class RedisSessionInterface(SessionInterface):
    serializer = pickle
    session_class = RedisSession

    def __init__(self, session_lifetime):
        # Should we just have one shared redis.Redis object?
        self.redis = redis
        self.key_prefix = key_prefix
        self.session_lifetime = session_lifetime

    def open_session(self, app, request):
        cookie_data = request.cookies.get(app.session_cookie_name)
        if not cookie_data:
            sid, key = self._generate_sid_and_key()
            return self.session_class(sid=sid, key=key,
                                      permanent=self.permanent)

        val = self.redis.get(self.key_prefix + sid)
        if val is not None:
            try:
                data = self.serializer.loads(val)
                return self.session_class(data, sid=sid, key=key)
            except:
                return self.session_class(sid=sid, key=key, permanent=self.permanent)
        return self.session_class(sid=sid, key=key, permanent=self.permanent)

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        if not session:
            if session.modified:
                self.redis.delete(self.key_prefix + session.sid)
                response.delete_cookie(app.session_cookie_name,
                                       domain=domain, path=path)
            return

        # Modification case.  There are upsides and downsides to
        # emitting a set-cookie header each request.  The behavior
        # is controlled by the :meth:`should_set_cookie` method
        # which performs a quick check to figure out if the cookie
        # should be set or not.  This is controlled by the
        # SESSION_REFRESH_EACH_REQUEST config flag as well as
        # the permanent flag on the session itself.
        if not self.should_set_cookie(app, session):
            return

        secure = self.get_cookie_secure(app)
        client = self.serializer.dumps(dict(session))
        self.redis.setex(name=self.key_prefix + session.sid, value=val,
                         time=total_seconds(app.permanent_session_lifetime))
        response.set_cookie(app.session_cookie_name, value=self.client_session,
                            httponly=True, domain=domain, path='/',
                            secure=secure)
