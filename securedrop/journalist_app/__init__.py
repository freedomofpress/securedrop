from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Tuple, Union

import i18n
import template_filters
import version
from actions.exceptions import NotFoundError
from db import db
from flask import Flask, abort, g, json, redirect, render_template, request, url_for
from flask_babel import gettext
from flask_wtf.csrf import CSRFError, CSRFProtect
from journalist_app import account, admin, api, col, main
from journalist_app.sessions import Session, session
from models import InstanceConfig
from sdconfig import SecureDropConfig
from werkzeug import Response
from werkzeug.exceptions import HTTPException, default_exceptions

_insecure_views = ["main.login", "static"]
_insecure_api_views = ["api.get_token", "api.get_endpoints"]
# Timezone-naive datetime format expected by SecureDrop Client
API_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def get_logo_url(app: Flask) -> str:
    if not app.static_folder:
        raise FileNotFoundError

    custom_logo_filename = "i/custom_logo.png"
    default_logo_filename = "i/logo.png"
    custom_logo_path = Path(app.static_folder) / custom_logo_filename
    default_logo_path = Path(app.static_folder) / default_logo_filename
    if custom_logo_path.is_file():
        return url_for("static", filename=custom_logo_filename)
    elif default_logo_path.is_file():
        return url_for("static", filename=default_logo_filename)

    raise FileNotFoundError


def create_app(config: SecureDropConfig) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(config.JOURNALIST_TEMPLATES_DIR.absolute()),
        static_folder=config.STATIC_DIR.absolute(),
    )

    app.config.from_object(config.JOURNALIST_APP_FLASK_CONFIG_CLS)

    Session(app)
    csrf = CSRFProtect(app)

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = config.DATABASE_URI
    db.init_app(app)

    class JSONEncoder(json.JSONEncoder):
        """Custom JSON encoder to use our preferred timestamp format"""

        def default(self, obj: "Any") -> "Any":
            if isinstance(obj, datetime):
                return obj.strftime(API_DATETIME_FORMAT)
            super().default(obj)

    app.json_encoder = JSONEncoder

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e: CSRFError) -> "Response":
        app.logger.error("The CSRF token is invalid.")
        msg = gettext("You have been logged out due to inactivity.")
        session.destroy(("error", msg), session.get("locale"))
        return redirect(url_for("main.login"))

    # Convert a NotFoundError raised by an action into a 404
    @app.errorhandler(NotFoundError)
    def handle_action_raised_not_found(e: NotFoundError) -> None:
        abort(404)

    def _handle_http_exception(
        error: HTTPException,
    ) -> Tuple[Union[Response, str], Optional[int]]:
        # Workaround for no blueprint-level 404/5 error handlers, see:
        # https://github.com/pallets/flask/issues/503#issuecomment-71383286
        # TODO: clean up API error handling such that all except 404/5s are
        # registered in the blueprint and 404/5s are handled at the application
        # level.
        if request.path.startswith("/api/"):
            handler = list(app.error_handler_spec["api"][error.code].values())[0]
            return handler(error)  # type: ignore

        return render_template("error.html", error=error), error.code

    for code in default_exceptions:
        app.errorhandler(code)(_handle_http_exception)

    i18n.configure(config, app)

    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    app.jinja_env.globals["version"] = version.__version__
    app.jinja_env.filters["rel_datetime_format"] = template_filters.rel_datetime_format
    app.jinja_env.filters["filesizeformat"] = template_filters.filesizeformat
    app.jinja_env.filters["html_datetime_format"] = template_filters.html_datetime_format
    app.jinja_env.add_extension("jinja2.ext.do")

    @app.before_request
    def update_instance_config() -> None:
        InstanceConfig.get_default(refresh=True)

    @app.before_request
    def setup_g() -> Optional[Response]:
        """Store commonly used values in Flask's special g object"""

        i18n.set_locale(config)

        if InstanceConfig.get_default().organization_name:
            g.organization_name = (  # pylint: disable=assigning-non-slot
                InstanceConfig.get_default().organization_name
            )
        else:
            g.organization_name = gettext("SecureDrop")  # pylint: disable=assigning-non-slot

        try:
            g.logo = get_logo_url(app)  # pylint: disable=assigning-non-slot
        except FileNotFoundError:
            app.logger.error("Site logo not found.")

        if request.path.split("/")[1] == "api":
            if request.endpoint not in _insecure_api_views and not session.logged_in():
                abort(403)
        else:
            if request.endpoint not in _insecure_views and not session.logged_in():
                return redirect(url_for("main.login"))

        if request.method == "POST":
            filesystem_id = request.form.get("filesystem_id")
            if filesystem_id:
                g.filesystem_id = filesystem_id  # pylint: disable=assigning-non-slot

        return None

    app.register_blueprint(main.make_blueprint())
    app.register_blueprint(account.make_blueprint(), url_prefix="/account")
    app.register_blueprint(admin.make_blueprint(), url_prefix="/admin")
    app.register_blueprint(col.make_blueprint(), url_prefix="/col")
    api_blueprint = api.make_blueprint()
    app.register_blueprint(api_blueprint, url_prefix="/api/v1")
    csrf.exempt(api_blueprint)

    return app
