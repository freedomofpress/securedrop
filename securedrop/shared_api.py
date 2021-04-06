import json
from uuid import UUID
import os

from flask import Request, Response, jsonify, abort

from sdconfig import config, SDConfig
from models import Source, Journalist, Group, GroupMember

from signal_groups.api.errors import ZkGroupException
from signal_groups.api.auth import AuthCredentialPresentation
from signal_groups.api.groups import GroupPublicParams
from signal_protocol.curve import PublicKey
from signal_protocol.sealed_sender import SenderCertificate

from typing import Optional, Tuple, Union


def server_public_params() -> Tuple[Response, int]:
    """
    Get server public parameters
    """
    response = jsonify({
        'server_public_params': config.server_public_params.serialize().hex(),
    })
    return response, 200


def auth_credential(user: Union[Source, Journalist]) -> Tuple[Response, int]:
    """
    Get auth_credential for user
    """
    randomness = os.urandom(32)

    # uid in 16 BE bytes
    uid = UUID(user.uuid).bytes

    redemption_time = 123456  # TODO
    auth_credential_response = config.server_secret_params.issue_auth_credential(
        randomness, uid, redemption_time
    )

    response = jsonify({
        'auth_credential': auth_credential_response.serialize().hex(),
    })
    return response, 200


def sender_cert(user: Union[Source, Journalist]) -> Tuple[Response, int]:
    """
    Get sender cert
    """
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


def auth_as_group_member(request: Request) -> Optional[Group]:
    req = json.loads(request.data.decode('utf-8'))
    raw_auth_credential_presentation = req.get('auth_credential_presentation', None)
    raw_group_public_params = req.get('group_public_params', None)

    if raw_auth_credential_presentation is None:
        abort(400, 'auth_credential_presentation not found in request body')
    if raw_group_public_params is None:
        abort(400, 'group_public_params field is missing')

    try:
        group_public_params = GroupPublicParams.deserialize(bytes.fromhex(raw_group_public_params))
    except ValueError:
        abort(400, 'err: could not deserialize GroupPublicParams')

    try:
        auth_credential_presentation = AuthCredentialPresentation.deserialize(bytes.fromhex(raw_auth_credential_presentation))
    except ValueError:
        abort(400, 'err: could not deserialize AuthCredentialPresentation')

    try:
        config.server_secret_params.verify_auth_credential_presentation(group_public_params, auth_credential_presentation)
    except ZkGroupException:
        return None

    # Does the GroupPublicParams correspond to an actual group?
    group_id = bytes(group_public_params.get_group_identifier())
    group = Group.query.filter_by(group_uid=group_id).first()
    if not group:
        return None

    # Does the UidCiphertext correspond to a user in that group?
    uuid_ciphertext = auth_credential_presentation.get_uuid_ciphertext()
    user = GroupMember.query.filter_by(uid_ciphertext=uuid_ciphertext.serialize()).first()
    if not user:  # User not found at all in _any_ group
        return None
    if user.group_id != group.id:  # User found, but not in _this_ group
        return None

    return group
