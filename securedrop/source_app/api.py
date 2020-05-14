import json
import platform

from flask import Blueprint, current_app, make_response

from source_app.utils import get_sourcev2_url, get_sourcev3_url

import version


def make_blueprint(config):
    view = Blueprint('api', __name__)

    @view.route('/metadata')
    def metadata():
        meta = {
            'allow_document_uploads': current_app.instance_config.allow_document_uploads,
            'gpg_fpr': config.JOURNALIST_KEY,
            'sd_version': version.__version__,
            'server_os': platform.linux_distribution()[1],
            'supported_languages': config.SUPPORTED_LOCALES,
            'v2_source_url': get_sourcev2_url(),
            'v3_source_url': get_sourcev3_url()
        }
        resp = make_response(json.dumps(meta))
        resp.headers['Content-Type'] = 'application/json'
        return resp

    return view
