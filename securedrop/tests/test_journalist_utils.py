# -*- coding: utf-8 -*-
from flask import url_for
import pytest
import random

from models import RevokedToken
from sqlalchemy.orm.exc import NoResultFound

from journalist_app.utils import cleanup_expired_revoked_tokens

from .utils.api_helper import get_api_headers

random.seed('◔ ⌣ ◔')


def test_revoke_token_cleanup_does_not_delete_tokens_if_not_expired(journalist_app, test_journo,
                                                                    journalist_api_token):
    with journalist_app.test_client() as app:
        resp = app.post(url_for('api.logout'), headers=get_api_headers(journalist_api_token))
        assert resp.status_code == 200

        cleanup_expired_revoked_tokens()

        revoked_token = RevokedToken.query.filter_by(token=journalist_api_token).one()
        assert revoked_token.journalist_id == test_journo['id']


def test_revoke_token_cleanup_does_deletes_tokens_that_are_expired(journalist_app, test_journo,
                                                                   journalist_api_token, mocker):
    with journalist_app.test_client() as app:
        resp = app.post(url_for('api.logout'), headers=get_api_headers(journalist_api_token))
        assert resp.status_code == 200

        # Mock response from expired token method when token is expired
        mocker.patch('journalist_app.admin.Journalist.validate_token_is_not_expired_or_invalid',
                     return_value=None)
        cleanup_expired_revoked_tokens()

        with pytest.raises(NoResultFound):
            RevokedToken.query.filter_by(token=journalist_api_token).one()
