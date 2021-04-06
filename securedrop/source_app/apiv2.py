from datetime import datetime, timedelta
import json
from uuid import UUID
import os

import flask
import werkzeug
from functools import wraps
from sqlalchemy import Column

from flask import Blueprint, current_app, make_response, jsonify, request, abort
from models import Group, GroupMember, Source, WrongPasswordException, Journalist, SourceMessage, JournalistReply, active_securedrop_groups
from werkzeug.exceptions import default_exceptions

from db import db
import shared_api
from sdconfig import config, SDConfig
from typing import Callable, Optional, Union, Dict, List, Any, Tuple

import signal_protocol

from signal_groups.api.auth import AuthCredentialPresentation
from signal_groups.api.groups import GroupPublicParams, UuidCiphertext
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

    @api.route('/groups', methods=['GET'])
    @token_required
    def groups() -> Tuple[flask.Response, int]:
        """
        Get SecureDrop group membership information. This lets a source know
        who is onboarded to each organization.
        """

        response = jsonify(active_securedrop_groups())
        return response, 200

    # This intentionally does not have @token_required, in the body of the
    # request, the user must present a valid AuthCredentialPresentation
    @api.route('/groups/members', methods=['POST'])
    def get_group_members() -> Tuple[flask.Response, int]:
        group = shared_api.auth_as_group_member(request)
        if group:
            members = GroupMember.query.filter_by(group_id=group.id).all()
            uuid_ciphertexts = [x.uid_ciphertext.hex() for x in members]
            response = jsonify({'members': uuid_ciphertexts})
            return response, 200
        else:
            abort(403, 'err: could not authenticate')

    # This intentionally does not have @token_required, in the body of the
    # request, the user must present a valid AuthCredentialPresentation
    @api.route('/groups/new', methods=['POST'])
    def create_group() -> Tuple[flask.Response, int]:
        """
        Create group
        """
        if request.json is None:
                abort(400, 'please send requests in valid JSON')

        req = json.loads(request.data.decode('utf-8'))
        raw_auth_credential_presentation = req.get('auth_credential_presentation', None)
        group_id = req.get('group_id', None)
        raw_group_public_params = req.get('group_public_params', None)
        group_members = req.get('group_members', [])
        group_admins = req.get('group_admins', [])

        if raw_auth_credential_presentation is None:
            abort(400, 'auth_credential_presentation not found in request body')
        if group_id is None:
            abort(400, 'group_id field is missing')
        if raw_group_public_params is None:
            abort(400, 'group_public_params field is missing')
        if not group_members:
            abort(400, 'group_members field is missing')
        if not group_admins:
            abort(400, 'group_admins field is missing')

        try:
            group_public_params = GroupPublicParams.deserialize(bytes.fromhex(raw_group_public_params))
        except ValueError:
            abort(400, 'err: could not deserialize GroupPublicParams')

        try:
            auth_credential_presentation = AuthCredentialPresentation.deserialize(bytes.fromhex(raw_auth_credential_presentation))
        except ValueError:
            abort(400, 'err: could not deserialize AuthCredentialPresentation')

        # Before doing anything, we must verify the auth credential presentation.
        config.server_secret_params.verify_auth_credential_presentation(group_public_params, auth_credential_presentation)

        group_creator_uuid_ciphertext = auth_credential_presentation.get_uuid_ciphertext()
        new_group_id = bytes(group_public_params.get_group_identifier())

        # We ensure the group_id is not already in use on the server.
        group = Group.query.filter_by(group_uid=new_group_id).first()
        if group:
            abort(400, 'err: group already exists')
        # This means that users can enumerate group_ids.
        # But, they can't do anything with that info unless they are the admin.
        new_group = Group(new_group_id, group_public_params.serialize())

        members_uuid_cipher_to_add = []
        admins_uuid_cipher_to_add = []

        for entry in group_members:
            members_uuid_cipher_to_add.append(bytes.fromhex(entry))

        for entry in group_admins:
            admins_uuid_cipher_to_add.append(bytes.fromhex(entry))

        # We check the Uidciphertext is making a group including themselves.
        # TODO: allow a third role "Admin" that create groups for Journalists and Sources (i.e.
        # without themselves in it)?
        if group_creator_uuid_ciphertext.serialize().hex() not in group_members + group_admins:
            abort(400, 'err: cannot create a group for others')

        # -- PERMISSIONS FOR GROUP CREATORS --
        # For sources, they must NOT be an admin.
        if group_creator_uuid_ciphertext.serialize().hex() in group_admins:
            abort(400, 'err: source group creators should not be admins')

        # -- PERMISSIONS FOR OTHER GROUP MEMBERS --
        # Server knows the group creator is the source, so all other users should be admins.
        if len(group_admins) != len(group_admins) + len(group_members) - 1:
            abort(400, 'err: all journalists should be admins')

        # Now that we've validated everything. Let's add the new objects to the database.
        db.session.add(new_group)
        db.session.commit()
        for member in members_uuid_cipher_to_add:
            db.session.add(GroupMember(new_group, member, is_admin=False))
        for admin in admins_uuid_cipher_to_add:
            db.session.add(GroupMember(new_group, admin, is_admin=True))
        db.session.commit()

        return jsonify({'message': 'Your group has been created'}), 200

    @api.route('/auth_credential', methods=['GET'])
    @token_required
    def auth_credential() -> Tuple[flask.Response, int]:
        user = _authenticate_user_from_auth_header(request)
        return shared_api.auth_credential(user)

    @api.route('/server_params', methods=['GET'])
    @token_required
    def server_public_params() -> Tuple[flask.Response, int]:
        return shared_api.server_public_params()

    @api.route('/sender_cert', methods=['GET'])
    @token_required
    def sender_cert() -> Tuple[flask.Response, int]:
        user = _authenticate_user_from_auth_header(request)
        return shared_api.sender_cert(user)

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
