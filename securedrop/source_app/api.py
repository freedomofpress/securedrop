import json

import flask
from flask import Blueprint, current_app, make_response

from sdconfig import SDConfig
from source_app.utils import get_sourcev2_url, get_sourcev3_url

import version


with open("/etc/lsb-release", "r") as f:
    server_os = f.readlines()[1].split("=")[1].strip("\n")


def make_blueprint(config: SDConfig) -> Blueprint:
    view = Blueprint('api', __name__)

    @view.route('/metadata')
    def metadata() -> flask.Response:
        meta = {
            'organization_name': current_app.instance_config.organization_name,
            'allow_document_uploads': current_app.instance_config.allow_document_uploads,
            'gpg_fpr': config.JOURNALIST_KEY,
            'sd_version': version.__version__,
            'server_os': server_os,
            'supported_languages': config.SUPPORTED_LOCALES,
            'v2_source_url': get_sourcev2_url(),
            'v3_source_url': get_sourcev3_url()
        }
        resp = make_response(json.dumps(meta))
        resp.headers['Content-Type'] = 'application/json'
        return resp

    return view
