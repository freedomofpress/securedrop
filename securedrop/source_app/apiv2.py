import json

import flask
from flask import Blueprint, current_app, make_response, jsonify

from sdconfig import SDConfig


def make_blueprint(config: SDConfig) -> Blueprint:
    """Source API"""
    api = Blueprint('apiv2', __name__)

    @api.route('/')
    def get_endpoints() -> flask.Response:
        endpoints = {'signal_registration_url': '/api/v2/register'}
        return jsonify(endpoints), 200

    return api
