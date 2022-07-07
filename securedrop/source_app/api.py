import json

import flask
import server_os
import version
from flask import Blueprint, make_response
from models import InstanceConfig
from sdconfig import SDConfig
from source_app.utils import get_sourcev3_url


def make_blueprint(config: SDConfig) -> Blueprint:
    view = Blueprint("api", __name__)

    @view.route("/metadata")
    def metadata() -> flask.Response:
        meta = {
            "organization_name": InstanceConfig.get_default().organization_name,
            "allow_document_uploads": InstanceConfig.get_default().allow_document_uploads,
            "gpg_fpr": config.JOURNALIST_KEY,
            "sd_version": version.__version__,
            "server_os": server_os.get_os_release(),
            "supported_languages": config.SUPPORTED_LOCALES,
            "v3_source_url": get_sourcev3_url(),
        }
        resp = make_response(json.dumps(meta))
        resp.headers["Content-Type"] = "application/json"
        return resp

    return view
