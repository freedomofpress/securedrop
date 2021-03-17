from datetime import datetime, timedelta
import json

import flask
import werkzeug
from functools import wraps
from sqlalchemy import Column

from flask import Blueprint, current_app, make_response, jsonify, request, abort
from models import Source, WrongPasswordException, Journalist, SourceMessage, JournalistReply
from werkzeug.exceptions import default_exceptions

from db import db
from sdconfig import config, SDConfig
from typing import Callable, Optional, Union, Dict, List, Any, Tuple
from source_app.utils import active_securedrop_groups

import signal_protocol

from signal_protocol.curve import PublicKey
from signal_protocol.sealed_sender import SenderCertificate

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


def get_or_404(model: db.Model, object_id: str, column: Column) -> db.Model:
    result = model.query.filter(column == object_id).one_or_none()
    if result is None:
        abort(404)
    return result


def token_required(f: Callable) -> Callable:
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        _authenticate_user_from_auth_header(request)
        return f(*args, **kwargs)
    return decorated_function


def make_blueprint(config: SDConfig) -> Blueprint:
    """Source API"""
    api = Blueprint('apiv2', __name__)


    # Before every post, we validate the payload before processing the request
    @api.before_request
    def validate_data() -> None:
        if request.method == 'POST':
            if not request.data:
                dataless_endpoints = [
                    'confirm_message'
                ]
                for endpoint in dataless_endpoints:
                    if request.endpoint == 'apiv2.' + endpoint:
                        return
                abort(400, 'malformed request')
            # other requests must have valid JSON payload
            else:
                try:
                    json.loads(request.data.decode('utf-8'))
                except (ValueError):
                    abort(400, 'malformed request')

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
        signed_prekey_id = creds.get('signed_prekey_id', None)
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
        if signed_prekey_id is None:
            abort(400, 'signed_prekey_id field is missing')

        # TODO: Server also verifies the prekey sig and rejects if invalid.
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
        user.signed_prekey_id = signed_prekey_id

        response = jsonify({
            'message': 'your account is now registered for messaging'
        })

        db.session.add(user)
        db.session.commit()

        return response, 200

    @api.route('/sender_cert', methods=['GET'])
    @token_required
    def sender_cert() -> Tuple[flask.Response, int]:
        """
        Get sender cert
        """
        user = _authenticate_user_from_auth_header(request)

        if not user.is_signal_registered():
            abort(400, 'your account is not registered')

        expiration = 123  # TODO: timestamp
        DEVICE_ID = 1
        sender_cert = SenderCertificate(
            user.uuid,
            user.uuid,
            PublicKey.deserialize(user.identity_key),
            DEVICE_ID,
            expiration,
            config.server_cert,
            config.server_key.private_key(),
        )
        response = jsonify({
            'sender_cert': sender_cert.serialized().hex(),
            'trust_root': config.trust_root.public_key().serialize().hex(),
        })
        return response, 200

    @api.route('/groups', methods=['GET'])
    @token_required
    def groups() -> Tuple[flask.Response, int]:
        """
        Get SecureDrop group membership information. This lets a source know
        who they should be encrypting their messages to on the journalist side.
        """
        response = jsonify(active_securedrop_groups())
        return response, 200

    @api.route('/journalists/<journalist_uuid>/prekey_bundle', methods=['GET'])
    @token_required
    def prekey_bundle(journalist_uuid: str) -> Tuple[flask.Response, int]:
        """
        Get a prekey bundle to start a new session with journalist_uuid.
        """
        # Threat: Enables source to enumerate journalist uuids
        # This endpoint also would need rate limiting as it allows an attacker to
        # potentially exhaust the one-time prekey supply.
        journalist = get_or_404(Journalist, journalist_uuid, column=Journalist.uuid)

        # TODO: Add one-time prekeys
        response = jsonify({
            'signed_prekey_id': journalist.signed_prekey_id,
            'journalist_uuid': journalist.uuid,
            'identity_key': journalist.identity_key.hex(),
            'signed_prekey': journalist.signed_prekey.hex(),
            'signed_prekey_timestamp': journalist.signed_prekey_timestamp,
            'prekey_signature': journalist.prekey_signature.hex(),
            'registration_id': journalist.registration_id,
        })
        return response, 200

    @api.route('/journalists/<journalist_uuid>/messages', methods=['POST'])
    @token_required
    def send_message(journalist_uuid: str) -> Tuple[flask.Response, int]:
        """
        Send a message to journalist_uuid.
        """
        if request.json is None:
                abort(400, 'please send requests in valid JSON')

        if 'message' not in request.json:
                abort(400, 'message not found in request body')

        user = _authenticate_user_from_auth_header(request)
        journalist = get_or_404(Journalist, journalist_uuid, column=Journalist.uuid)

        data = request.json
        if not data['message']:
            abort(400, 'message should not be empty')

        message = SourceMessage(journalist, data['message'])
        db.session.add(message)
        db.session.commit()
        return jsonify({'message': 'Your message has been stored'}), 200

    @api.route('/messages', methods=['GET'])
    @token_required
    def get_message() -> Tuple[flask.Response, int]:
        """
        Get messages from journalists.

        TODO: Pagination
        """
        user = _authenticate_user_from_auth_header(request)
        reply = JournalistReply.query.filter_by(source_id=user.id).first()
        if reply:
            return jsonify({
                "resp": "NEW_MSG",
                "message_uuid": reply.uuid,
                "message": reply.message.hex(),
            }), 200
        else:
            return jsonify({"resp": "NO_MSG"}), 200

    @api.route('/messages/confirmation/<message_uuid>', methods=['POST'])
    @token_required
    def confirm_message(message_uuid: str) -> Tuple[flask.Response, int]:
        """
        Confirm receipt of message_uuid.
        """
        user = _authenticate_user_from_auth_header(request)
        reply = JournalistReply.query.filter_by(uuid=message_uuid).first()

        # TODO: the timing of response reveals which of these two scenarios is happening
        # Source trying to delete another's message
        if reply.source_id != user.id:
            abort(404, 'message not found with this (source uuid, message uuid) pair')

        if not reply:  # Legit 404 (could replace with get_or_404, but wanted to customize message)
            abort(404, 'message not found with this (source uuid, message uuid) pair')

        # Message confirmed received by client. Remove from server.
        db.session.delete(reply)
        db.session.commit()
        return jsonify({'message': 'Confirmed receipt of message'}), 200

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
