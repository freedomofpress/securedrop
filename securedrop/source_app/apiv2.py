from datetime import datetime, timedelta
import json

import flask
import werkzeug
from functools import wraps

from flask import Blueprint, current_app, make_response, jsonify, request, abort
from models import Source, WrongPasswordException
from werkzeug.exceptions import default_exceptions

from db import db
from sdconfig import SDConfig
from typing import Callable, Optional, Union, Dict, List, Any, Tuple

TOKEN_EXPIRATION_MINS = 60 * 8

def _authenticate_user_from_auth_header(request: flask.Request) -> Source:
    try:
        auth_header = request.headers['Authorization']
    except KeyError:
        return abort(403, 'API token not found in Authorization header.')

    if auth_header:
        split = auth_header.split(" ")
        if len(split) != 2 or split[0] != 'Token':
            abort(403, 'Malformed authorization header.')
        auth_token = split[1]
    else:
        auth_token = ''
    authenticated_user = Source.validate_api_token_and_get_user(auth_token)
    if not authenticated_user:
        return abort(403, 'API token is invalid or expired.')
    return authenticated_user


def token_required(f: Callable) -> Callable:
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        _authenticate_user_from_auth_header(request)
        return f(*args, **kwargs)
    return decorated_function


def make_blueprint(config: SDConfig) -> Blueprint:
    """Source API"""
    api = Blueprint('apiv2', __name__)

    # TODO: rate limit source login
    @api.route('/token', methods=['POST'])
    def get_token() -> Tuple[flask.Response, int]:
        creds = json.loads(request.data.decode('utf-8'))

        passphrase = creds.get('passphrase', None)

        if passphrase is None:
            abort(400, 'passphrase field is missing')

        try:
            source = Source.login(passphrase)
            if not source:
                return abort(403, 'Token authentication failed.')
            token_expiry = datetime.utcnow() + timedelta(
                seconds=TOKEN_EXPIRATION_MINS * 60)

            response = jsonify({
                'token': source.generate_api_token(expiration=TOKEN_EXPIRATION_MINS * 60),
                'expiration': token_expiry.isoformat() + 'Z',
                'source_uuid': source.uuid,
            })

            return response, 200
        except WrongPasswordException:
            return abort(403, 'Token authentication failed.')

    @api.route('/')
    def get_endpoints() -> flask.Response:
        endpoints = {'signal_registration_url': '/api/v2/register'}
        return jsonify(endpoints), 200

    @api.route('/register', methods=['POST'])
    @token_required
    def signal_registration() -> Tuple[flask.Response, int]:
        """
        Almost duplicate of journalist apiv2 (except for object)
        """
        user = _authenticate_user_from_auth_header(request)

        # TODO: Think about how best to handle users re-registering.
        if user.is_signal_registered():
            abort(400, 'your account is already registered')

        creds = json.loads(request.data.decode('utf-8'))
        identity_key = creds.get('identity_key', None)
        signed_prekey = creds.get('signed_prekey', None)
        signed_prekey_timestamp = creds.get('signed_prekey_timestamp', None)
        prekey_signature = creds.get('prekey_signature', None)
        registration_id = creds.get('registration_id', None)
        # TODO: handle OT prekeys

        if identity_key is None:
            abort(400, 'identity_key field is missing')
        if signed_prekey is None:
            abort(400, 'signed_prekey field is missing')
        if signed_prekey_timestamp is None:
            abort(400, 'signed_prekey_timestamp field is missing')
        if prekey_signature is None:
            abort(400, 'prekey_signature field is missing')
        if registration_id is None:
            abort(400, 'registration_id field is missing')

        # TODO: Server _could_ also verify the prekey sig and reject.
        # Clients will be doing this too on their end, but we could also do here.

        # This enables enumeration of in-use registration ids. This is fine since these are public.
        duplicate_reg_id = Source.query.filter_by(registration_id=registration_id).all()
        if duplicate_reg_id:
            abort(400, 'registration_id is in use')

        if user.signed_prekey_timestamp and user.signed_prekey_timestamp > signed_prekey_timestamp:
            abort(400, 'signed prekey timestamp should be fresher than what is on the server')

        user.identity_key = identity_key
        user.signed_prekey = signed_prekey
        user.signed_prekey_timestamp = signed_prekey_timestamp
        user.prekey_signature = prekey_signature
        user.registration_id = registration_id

        response = jsonify({
            'message': 'your account is now registered for messaging'
        })

        db.session.add(user)
        db.session.commit()

        return response, 200

    def _handle_api_http_exception(
        error: werkzeug.exceptions.HTTPException
    ) -> Tuple[flask.Response, int]:
        # Workaround for no blueprint-level 404/5 error handlers, see:
        # https://github.com/pallets/flask/issues/503#issuecomment-71383286
        response = jsonify({'error': error.name,
                           'message': error.description})

        return response, error.code  # type: ignore

    for code in default_exceptions:
        api.errorhandler(code)(_handle_api_http_exception)

    return api
