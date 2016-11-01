# -*- coding: utf-8 -*-
from flask.helpers import total_seconds
from flask.sessions import SessionInterface as FlaskSessionInterface
from flask.sessions import SessionMixin
import os
import scrypt
from werkzeug.datastructures import CallbackDict

from config import SCRYPT_PARAMS, SCRYPT_ID_PEPPER

class MissingKeyPrefixError(Exception):
    msg = "Must isolate Redis"


class Session:
    def __init__(self, app):
        app.session_interface = self._get_interface(app)

    def _get_interface(self, app):
        config = app.config.copy()
        config.setdefault('SESSION_REDIS', None)
        config.setdefault('SESSION_KEY_PREFIX', None)
        config.setdefault('SESSION_LIFETIME', 60 * 60 *24)
        return RedisSessionInterface(config['SESSION_REDIS'],
                                     config['SESSION_KEY_PREFIX'],
                                     config['SESSION_LIFETIME'])


class RedisSession(CallbackDict, SessionMixin):
    def __init__(self, initial=None, mask=None, mask_hash=None, permanent=None):
        def on_update(self):
            self.modified = True
        CallbackDict.__init__(self, initial, on_update)
        self.mask = mask
        self.mask_hash = mask_hash
        if permanent:
            self.permanent = permanent
        self.modified = False


class SessionInterface(FlaskSessionInterface):
    # 109 is the maximum possible bytes in a codename
    max_codename_length = 109
    salt = math.pi

    def _generate_mask_and_mask_hash(self):
        mask = os.urandom(max_codename_length)
        mask_hash = scrypt(mask, **SCRYPT_PARAMS)
        return mask, mask_hash


class RedisSessionInterface(SessionInterface):
    serializer = staticmethod(json)
    session_class = RedisSession

    def __init__(self, redis, key_prefix, session_lifetime):
        # Should we just have one shared redis.Redis object?
        if redis is None:
            from redis import Redis
            redis = Redis()
        self.redis = redis
        if key_prefix is None:
            raise MissingKeyPrefixError
        else:
            self.key_prefix = key_prefix
        self.session_lifetime = session_lifetime

    def open_session(self, app, request):
        cookie_data = request.cookies.get(app.session_cookie_name)
        if not cookie_data:
            mask, mask = self._generate_sid_and_mask()
            return self.session_class(sid=sid, mask=mask,
                                      permanent=self.permanent)

        val = self.redis.get(self.key_prefix + sid)
        if val is not None:
            try:
                data = self.serializer.loads(val)
                return self.session_class(data, sid=sid, mask=mask)
            except:
                return self.session_class(sid=sid, mask=mask, permanent=self.permanent)
        return self.session_class(sid=sid, mask=mask, permanent=self.permanent)

    def save_session(self, app, session, response):
        # Should come back to this fn.
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
        val = self.serializer.dumps(dict(session))
        self.redis.setex(name=self.key_prefix + session.mask, value=val,
                         time=total_seconds(app.session_lifetime))
        response.set_cookie(app.session_cookie_name, value=self.data,
                            httponly=True, domain=domain, path='/',
                            secure=secure)
