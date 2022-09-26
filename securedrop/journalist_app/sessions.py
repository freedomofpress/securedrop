import typing
from datetime import datetime, timedelta, timezone
from json.decoder import JSONDecodeError
from secrets import token_urlsafe
from typing import Any, Dict, Optional, Tuple

from flask import Flask, Request, Response
from flask import current_app as app
from flask.sessions import SessionInterface as FlaskSessionInterface
from flask.sessions import SessionMixin, session_json_serializer
from flask_babel import gettext
from itsdangerous import BadSignature, URLSafeTimedSerializer
from models import Journalist
from redis import Redis
from werkzeug.datastructures import CallbackDict


class ServerSideSession(CallbackDict, SessionMixin):
    """Baseclass for server-side based sessions."""

    def __init__(self, sid: str, token: str, lifetime: int = 0, initial: Any = None) -> None:
        def on_update(self: ServerSideSession) -> None:
            self.modified = True

        if initial and "uid" in initial:
            self.set_uid(initial["uid"])
            self.set_user()
        else:
            self.uid: Optional[int] = None
            self.user = None
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.token: str = token
        self.lifetime = lifetime
        self.is_api = False
        self.to_destroy = False
        self.to_regenerate = False
        self.modified = False
        self.flash: Optional[Tuple[str, str]] = None
        self.locale: Optional[str] = None

    def get_token(self) -> Optional[str]:
        return self.token

    def get_lifetime(self) -> datetime:
        return datetime.now(timezone.utc) + timedelta(seconds=self.lifetime)

    def set_user(self) -> None:
        if self.uid is not None:
            self.user = Journalist.query.get(self.uid)
        if self.user is None:
            # The uid has no match in the database, and this should really not happen
            self.uid = None
            self.to_destroy = True

    def get_user(self) -> Optional[Journalist]:
        return self.user

    def get_uid(self) -> Optional[int]:
        return self.uid

    def set_uid(self, uid: int) -> None:
        self.user = None
        self.uid = uid

    def logged_in(self) -> bool:
        if self.uid is not None:
            return True
        else:
            return False

    def destroy(
        self, flash: Optional[Tuple[str, str]] = None, locale: Optional[str] = None
    ) -> None:
        # The parameters are needed to pass the information to the new session
        self.locale = locale
        self.flash = flash
        self.uid = None
        self.user = None
        self.to_destroy = True

    def regenerate(self) -> None:
        self.to_regenerate = True


class SessionInterface(FlaskSessionInterface):
    def _generate_sid(self) -> str:
        return token_urlsafe(32)

    def _get_signer(self, app: Flask) -> URLSafeTimedSerializer:
        if not app.secret_key:
            raise RuntimeError("No secret key set")
        return URLSafeTimedSerializer(app.secret_key, salt=self.salt)

    """Uses the Redis key-value store as a session backend.

    :param redis: A ``redis.Redis`` instance.
    :param key_prefix: A prefix that is added to all Redis store keys.
    :param salt: Allows to set the signer salt from the calling interface
    :param header_name: if use_header, set the header name to parse
    """

    def __init__(
        self,
        lifetime: int,
        renew_count: int,
        redis: Redis,
        key_prefix: str,
        salt: str,
        header_name: str,
    ) -> None:
        self.serializer = session_json_serializer
        self.redis = redis
        self.lifetime = lifetime
        self.renew_count = renew_count
        self.key_prefix = key_prefix
        self.api_key_prefix = "api_" + key_prefix
        self.salt = salt
        self.api_salt = "api_" + salt
        self.header_name = header_name
        self.new = False
        self.has_same_site_capability = hasattr(self, "get_cookie_samesite")

    def _new_session(self, is_api: bool = False, initial: Any = None) -> ServerSideSession:
        sid = self._generate_sid()
        token: str = self._get_signer(app).dumps(sid)  # type: ignore
        session = ServerSideSession(sid=sid, token=token, lifetime=self.lifetime, initial=initial)
        session.new = True
        session.is_api = is_api
        return session

    def open_session(self, app: Flask, request: Request) -> Optional[ServerSideSession]:
        """This function is called by the flask session interface at the
        beginning of each request.
        """
        is_api = request.path.split("/")[1] == "api"

        if is_api:
            self.key_prefix = self.api_key_prefix
            self.salt = self.api_salt
            auth_header = request.headers.get(self.header_name)
            if auth_header:
                split = auth_header.split(" ")
                if len(split) != 2 or split[0] != "Token":
                    return self._new_session(is_api)
                sid: Optional[str] = split[1]
            else:
                return self._new_session(is_api)
        else:
            sid = request.cookies.get(app.session_cookie_name)
        if sid:
            try:
                sid = self._get_signer(app).loads(sid)
            except BadSignature:
                sid = None
        if not sid:
            return self._new_session(is_api)

        val = self.redis.get(self.key_prefix + sid)
        if val is not None:
            try:
                data = self.serializer.loads(val.decode("utf-8"))
                token: str = self._get_signer(app).dumps(sid)  # type: ignore
                return ServerSideSession(sid=sid, token=token, initial=data)
            except (JSONDecodeError, NotImplementedError):
                return self._new_session(is_api)
        # signed session_id provided in cookie is valid, but the session is not on the server
        # anymore so maybe here is the code path for a meaningful error message
        msg = gettext("You have been logged out due to inactivity.")
        return self._new_session(is_api, initial={"_flashes": [("error", msg)]})

    def save_session(  # type: ignore[override] # noqa
        self, app: Flask, session: ServerSideSession, response: Response
    ) -> None:
        """This is called at the end of each request, just
        before sending the response.
        """
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        if session.to_destroy:
            initial: Dict[str, Any] = {"locale": session.locale}
            if session.flash:
                initial["_flashes"] = [session.flash]
            self.redis.delete(self.key_prefix + session.sid)
            if not session.is_api:
                # Instead of deleting the cookie and send a new sid with the next request
                # create the new session already, so we can pass along messages and locale
                session = self._new_session(False, initial=initial)
        expires = self.redis.ttl(name=self.key_prefix + session.sid)
        if session.new:
            session["renew_count"] = self.renew_count
            expires = self.lifetime
        else:
            if expires < (30 * 60) and session["renew_count"] > 0:
                session["renew_count"] -= 1
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
            session.token = self._get_signer(app).dumps(session.sid)  # type: ignore
        if session.new or session.to_regenerate:
            self.redis.setex(name=self.key_prefix + session.sid, value=val, time=expires)
        elif session.modified:
            # To prevent race conditions where session is delete by an admin in the middle of a req
            # accept to save the session object if and only if alrady exists using the xx flag
            self.redis.set(name=self.key_prefix + session.sid, value=val, ex=expires, xx=True)
        if not session.is_api and (session.new or session.to_regenerate):
            response.headers.add("Vary", "Cookie")
            response.set_cookie(
                app.session_cookie_name,
                session.token,
                httponly=httponly,
                domain=domain,
                path=path,
                secure=secure,
                **conditional_cookie_kwargs  # type: ignore
            )

    def logout_user(self, uid: int) -> None:
        for key in self.redis.keys(self.key_prefix + "*") + self.redis.keys(
            "api_" + self.key_prefix + "*"
        ):
            found = self.redis.get(key)
            if found:
                sess = session_json_serializer.loads(found.decode("utf-8"))
                if "uid" in sess and sess["uid"] == uid:
                    self.redis.delete(key)


class Session:
    def __init__(self, app: Flask) -> None:
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> "None":
        """This is used to set up session for your app object.
        :param app: the Flask app object with proper configuration.
        """
        app.session_interface = self._get_interface(app)  # type: ignore

    def _get_interface(self, app: Flask) -> SessionInterface:
        config = app.config.copy()
        config.setdefault("SESSION_REDIS", Redis())
        config.setdefault("SESSION_LIFETIME", 2 * 60 * 60)
        config.setdefault("SESSION_RENEW_COUNT", 5)
        config.setdefault("SESSION_SIGNER_SALT", "session")
        config.setdefault("SESSION_KEY_PREFIX", "session:")
        config.setdefault("SESSION_HEADER_NAME", "authorization")

        session_interface = SessionInterface(
            config["SESSION_LIFETIME"],
            config["SESSION_RENEW_COUNT"],
            config["SESSION_REDIS"],
            config["SESSION_KEY_PREFIX"],
            config["SESSION_SIGNER_SALT"],
            config["SESSION_HEADER_NAME"],
        )

        return session_interface


# Re-export flask.session, but with the correct type information for mypy.
from flask import session  # noqa

session = typing.cast(ServerSideSession, session)
