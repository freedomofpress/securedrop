import json

from flask import abort, Blueprint, jsonify, request

import config
from models import Journalist


def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            auth_header = request.headers.get('Authorization')
        except:
            return abort(403, 'API token not found in Authorization header.')

        if auth_header:
            auth_token = auth_header.split(" ")[1]
        else:
            auth_token = ''
        if not Journalist.verify_api_token(auth_token):
            return abort(403, 'API token is invalid or expired.')
        return f(*args, **kwargs)
    return decorated_function


def make_blueprint(config):
    api = Blueprint('api', __name__)

    @api.route('/')
    def get_endpoints():
        endpoints = {'sources_url': '/api/v1/sources/',
                     'current_user_url': '/api/v1/user/',
                     'submissions_url': '/api/v1/submissions/',
                     'auth_token_url': '/api/v1/token/'}
        return jsonify(endpoints), 200

    @api.route('/token/', methods=['POST'])
    def get_token():
        creds = json.loads(request.data)
        username = creds['username']
        password = creds['password']
        one_time_code = creds['one_time_code']
        try:
            journalist = Journalist.login(username, password, one_time_code)
            return jsonify({'token': journalist.generate_api_token(
                 expiration=1800), 'expiration': 1800}), 200
        except:
            return abort(403, 'Token authentication failed.')

    return api
