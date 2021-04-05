from uuid import UUID
import os

from flask import Response, jsonify

from sdconfig import config, SDConfig
from models import Source, Journalist

from signal_protocol.curve import PublicKey
from signal_protocol.sealed_sender import SenderCertificate

from typing import Tuple, Union


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
