from datetime import datetime, timedelta
from secrets import token_urlsafe
from flask import Flask, Request, Response
from typing import Optional, Any
from flask.sessions import SessionInterface as FlaskSessionInterface
from flask.sessions import SessionMixin, session_json_serializer
from json.decoder import JSONDecodeError
from redis import Redis
from werkzeug.datastructures import CallbackDict
from itsdangerous import URLSafeTimedSerializer, BadSignature


class ServerSideSession(CallbackDict, SessionMixin):
    """Baseclass for server-side based sessions."""

    def __init__(self, sid: 'str', initial: 'Any' = None) -> 'None':
        def on_update(self: ServerSideSession) -> None:
            self.modified = True
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.token = None
        self.is_api = False
        self.to_destroy = False
        self.to_regenerate = False
        self.modified = False


class RedisSession(ServerSideSession):
    def get_token(self) -> Optional['str']:
        return self.token

    def get_lifetime(self) -> 'datetime':
        return datetime.utcnow() + timedelta(seconds=2 * 60 * 60)

    def destroy(self) -> 'None':
        self.to_destroy = True

    def regenerate(self) -> 'None':
        self.to_regenerate = True


class SessionInterface(FlaskSessionInterface):

    def _generate_sid(self) -> 'str':
        return token_urlsafe(32)

    def _get_signer(self, app: 'Flask') -> 'URLSafeTimedSerializer':
        return URLSafeTimedSerializer(app.secret_key,
                                      salt=self.salt)


class RedisSessionInterface(SessionInterface):
    """Uses the Redis key-value store as a session backend.

    :param redis: A ``redis.Redis`` instance.
    :param key_prefix: A prefix that is added to all Redis store keys.
    :param salt: Allows to set the signer salt from the calling interface
    :param header_name: if use_header, set the header name to parse
    """

    session_class = RedisSession

    def __init__(self, lifetime: 'int', renew_count: 'int', redis: 'Optional[Redis]',
                 key_prefix: 'str', salt: 'str', header_name: 'str') -> 'None':
        self.serializer = session_json_serializer
        if redis is None:
            redis = Redis()
        self.redis = redis
        self.lifetime = lifetime
        self.renew_count = renew_count
        self.key_prefix = key_prefix
        self.api_key_prefix = 'api_' + key_prefix
        self.salt = salt
        self.api_salt = 'api_' + salt
        self.header_name = header_name
        self.new = False
        self.has_same_site_capability = hasattr(self, "get_cookie_samesite")

    def open_session(self, app: 'Flask', request: 'Request') -> 'Optional[SessionMixin]':
        '''This function is called by the flask session interface at the
        beginning of each request.
        '''
        is_api = (request.path.split('/')[1] == 'api')

        def new_session(is_api: 'bool' = False) -> 'SessionMixin':
            sid = self._generate_sid()
            session = self.session_class(sid=sid)
            session.token = self._get_signer(app).dumps(sid)
            session.new = True
            session.is_api = is_api
            return session

        if not is_api:
            sid = request.cookies.get(app.session_cookie_name)
        else:
            self.key_prefix = self.api_key_prefix
            self.salt = self.api_salt
            sid = request.headers.get(self.header_name)
        if not sid:
            return new_session(is_api)
        try:
            sid = self._get_signer(app).loads(sid)
        except BadSignature:
            return new_session(is_api)

        val = self.redis.get(self.key_prefix + sid)
        if val is not None:
            try:
                data = self.serializer.loads(val)
                return self.session_class(sid=sid, initial=data)
            except (JSONDecodeError, NotImplementedError):
                return new_session(is_api)
        return new_session(is_api)

    def save_session(self, app: 'Flask', session: 'SessionMixin', response: 'Response') -> 'None':
        '''This is called at the end of each request, just
        before sending the response.
        '''
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        if session.to_destroy:
            self.redis.delete(self.key_prefix + session.sid)
            if not session.is_api:
                response.delete_cookie(app.session_cookie_name,
                                       domain=domain, path=path)
            return
        expires = self.redis.ttl(name=self.key_prefix + session.sid)
        if session.new:
            session['renew_count'] = self.renew_count
            expires = self.lifetime
        else:
            if expires < (30 * 60) and session['renew_count'] > 0:
                session['renew_count'] -= 1
                expires += self.lifetime
                session.modified = True
        conditional_cookie_kwargs = {}
        httponly = self.get_cookie_httponly(app)
        secure = self.get_cookie_secure(app)
        if self.has_same_site_capability:
            conditional_cookie_kwargs["samesite"] = self.get_cookie_samesite(app)
        val = self.serializer.dumps(dict(session))
        if session.to_regenerate:
            self.redis.delete(self.key_prefix + session.sid)
            session.sid = self._generate_sid()
            session.token = self._get_signer(app).dumps(session.sid)
        if session.modified or session.new:
            self.redis.setex(name=self.key_prefix + session.sid, value=val,
                             time=expires)
        if not session.is_api and (session.new or session.to_regenerate):
            response.set_cookie(app.session_cookie_name, session.token,
                                httponly=httponly, domain=domain, path=path,
                                secure=secure, **conditional_cookie_kwargs)


class Session(object):

    def __init__(self, app: 'Optional[Flask]' = None) -> 'None':
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app: 'Flask') -> 'None':
        """This is used to set up session for your app object.
        :param app: the Flask app object with proper configuration.
        """
        app.session_interface = self._get_interface(app)

    def _get_interface(self, app: 'Flask') -> 'RedisSessionInterface':
        config = app.config.copy()
        config.setdefault('SESSION_REDIS', None)
        config.setdefault('SESSION_LIFETIME', 2 * 60 * 60)
        config.setdefault('SESSION_RENEW_COUNT', 5)
        config.setdefault('SESSION_SIGNER_SALT', 'session')
        config.setdefault('SESSION_KEY_PREFIX', 'session:')
        config.setdefault('SESSION_HEADER_NAME', 'authorization')

        session_interface = RedisSessionInterface(
            config['SESSION_LIFETIME'], config['SESSION_RENEW_COUNT'],
            config['SESSION_REDIS'], config['SESSION_KEY_PREFIX'],
            config['SESSION_SIGNER_SALT'], config['SESSION_HEADER_NAME'])

        return session_interface
