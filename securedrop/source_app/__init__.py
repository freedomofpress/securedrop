import os
import time
from pathlib import Path
from typing import Optional, Tuple

import i18n
import template_filters
import version
import werkzeug
from db import db
from flask import Flask, g, make_response, redirect, render_template, request, session, url_for
from flask_babel import gettext
from flask_wtf.csrf import CSRFError, CSRFProtect
from models import InstanceConfig
from request_that_secures_file_uploads import RequestThatSecuresFileUploads
from sdconfig import SecureDropConfig
from source_app import api, info, main
from source_app.decorators import ignore_static
from source_app.utils import clear_session_and_redirect_to_logged_out_page
from startup import validate_journalist_key


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
        template_folder=str(config.SOURCE_TEMPLATES_DIR.absolute()),
        static_folder=config.STATIC_DIR.absolute(),
    )
    app.request_class = RequestThatSecuresFileUploads
    app.config.from_object(config.SOURCE_APP_FLASK_CONFIG_CLS)

    i18n.configure(config, app)

    @app.before_request
    @ignore_static
    def setup_i18n() -> None:
        """Store i18n-related values in Flask's special g object"""
        i18n.set_locale(config)

    # The default CSRF token expiration is 1 hour. Since large uploads can
    # take longer than an hour over Tor, we increase the valid window to 24h.
    app.config["WTF_CSRF_TIME_LIMIT"] = 60 * 60 * 24
    CSRFProtect(app)
    app.config["SESSION_COOKIE_SAMESITE"] = "Strict"

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = config.DATABASE_URI
    db.init_app(app)

    # Check if the Submission Key is valid; if not, we'll disable the UI
    app.config["SUBMISSION_KEY_VALID"] = validate_journalist_key()

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e: CSRFError) -> werkzeug.Response:
        return clear_session_and_redirect_to_logged_out_page(flask_session=session)

    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    app.jinja_env.globals["version"] = version.__version__
    # Exported to source templates for being included in instructions
    app.jinja_env.globals["submission_key_fpr"] = config.JOURNALIST_KEY
    app.jinja_env.filters["rel_datetime_format"] = template_filters.rel_datetime_format
    app.jinja_env.filters["nl2br"] = template_filters.nl2br
    app.jinja_env.filters["filesizeformat"] = template_filters.filesizeformat
    app.jinja_env.filters["html_datetime_format"] = template_filters.html_datetime_format
    app.jinja_env.add_extension("jinja2.ext.do")

    for module in [main, info, api]:
        app.register_blueprint(module.make_blueprint(config))  # type: ignore

    # before_request hooks are executed in order of declaration, so set up g object
    # before the potential tor2web 403 response.
    @app.before_request
    @ignore_static
    def setup_g() -> Optional[werkzeug.Response]:
        if InstanceConfig.get_default(refresh=True).organization_name:
            g.organization_name = (  # pylint: disable=assigning-non-slot
                InstanceConfig.get_default().organization_name
            )
        else:
            g.organization_name = gettext("SecureDrop")  # pylint: disable=assigning-non-slot

        try:
            g.logo = get_logo_url(app)  # pylint: disable=assigning-non-slot
        except FileNotFoundError:
            app.logger.error("Site logo not found.")

        return None

    @app.before_request
    @ignore_static
    def check_tor2web() -> Optional[werkzeug.Response]:
        # TODO: expand header checking logic to catch modern tor2web proxies
        if "X-tor2web" in request.headers and request.path != url_for("info.tor2web_warning"):
            return redirect(url_for("info.tor2web_warning"))
        return None

    @app.before_request
    @ignore_static
    def check_submission_key() -> Optional[werkzeug.Response]:
        if not app.config["SUBMISSION_KEY_VALID"]:
            session.clear()
            g.show_offline_message = True
            return make_response(render_template("offline.html"), 503)
        return None

    @app.errorhandler(404)
    def page_not_found(error: werkzeug.exceptions.HTTPException) -> Tuple[str, int]:
        return render_template("notfound.html"), 404

    @app.errorhandler(500)
    def internal_error(error: werkzeug.exceptions.HTTPException) -> Tuple[str, int]:
        return render_template("error.html"), 500

    # Obscure the creation time of source private keys by touching them all
    # on startup.
    private_keys = config.GPG_KEY_DIR / "private-keys-v1.d"
    # The folder may not exist yet in some dev/testing setups,
    # and if it doesn't exist there's no mtime to obscure.
    if private_keys.is_dir():
        now = time.time()
        for entry in os.scandir(private_keys):
            if not entry.is_file() or not entry.name.endswith(".key"):
                continue
            os.utime(entry.path, times=(now, now))
            # So the ctime is also updated
            os.chmod(entry.path, entry.stat().st_mode)

    return app
