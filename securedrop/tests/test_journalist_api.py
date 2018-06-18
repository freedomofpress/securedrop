# -*- coding: utf-8 -*-
import json
import os
import pytest

from pyotp import TOTP

from flask import url_for

from models import Journalist

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
from sdconfig import SDConfig, config
from utils.api_helper import get_api_headers


def test_unauthenticated_user_gets_all_endpoints(journalist_app):
    with journalist_app.test_client() as app:
        response = app.get(url_for('api.get_endpoints'),
                           content_type='application/json')

        observed_endpoints = json.loads(response.data)

        for expected_endpoint in ['current_user_url', 'sources_url',
                                  'submissions_url']:
            assert expected_endpoint in observed_endpoints.keys()


def test_valid_user_can_get_an_api_token(journalist_app, test_journo):
    with journalist_app.test_client() as app:
        valid_token = TOTP(test_journo['otp_secret']).now()
        response = app.post(url_for('api.get_token'),
                            data=json.dumps(
                                {'username': test_journo['username'],
                                 'password': test_journo['password'],
                                 'one_time_code': valid_token}),
                            headers=get_api_headers())
        observed_response = json.loads(response.data)

        assert isinstance(Journalist.verify_api_token(observed_response['token']),
                          Journalist) is True
        assert response.status_code == 200


def test_user_cannot_get_an_api_token_with_wrong_password(journalist_app,
                                                          test_journo):
    with journalist_app.test_client() as app:
        valid_token = TOTP(test_journo['otp_secret']).now()
        response = app.post(url_for('api.get_token'),
                            data=json.dumps(
                                {'username': test_journo['username'],
                                 'password': 'wrong password',
                                 'one_time_code': valid_token}),
                            headers=get_api_headers())
        observed_response = json.loads(response.data)

        assert response.status_code == 403
        assert observed_response['error'] == 'forbidden'


def test_user_cannot_get_an_api_token_with_wrong_2fa_token(journalist_app,
                                                           test_journo):
    with journalist_app.test_client() as app:
        response = app.post(url_for('api.get_token'),
                            data=json.dumps(
                                {'username': test_journo['username'],
                                 'password': test_journo['password'],
                                 'one_time_code': '123456'}),
                            headers=get_api_headers())
        observed_response = json.loads(response.data)

        assert response.status_code == 403
        assert observed_response['error'] == 'forbidden'


def test_authorized_user_gets_all_sources(journalist_app, test_source,
                                          journalist_api_token):
    with journalist_app.test_client() as app:
        response = app.get(url_for('api.get_all_sources'),
                           headers=get_api_headers(journalist_api_token))

        data = json.loads(response.data)

        assert response.status_code == 200

        # We expect to see our test source in the response
        assert test_source['source'].journalist_designation == \
            data['sources'][0]['journalist_designation']


def test_user_without_token_cannot_get_protected_endpoints(journalist_app,
                                                           test_source):
    with journalist_app.app_context():
        protected_routes = [
            url_for('api.get_all_sources'),
            url_for('api.single_source', source_id=test_source['source'].id),
            url_for('api.all_source_submissions',
                    source_id=test_source['source'].id),
            url_for('api.single_submission',
                    source_id=test_source['source'].id,
                    submission_id=test_source['submissions'][0].id),
            url_for('api.download_submission',
                    source_id=test_source['source'].id,
                    submission_id=test_source['submissions'][0].id),
            ]

    with journalist_app.test_client() as app:
        for protected_route in protected_routes:
            response = app.get(protected_route,
                               headers=get_api_headers(''))

            assert response.status_code == 403


def test_user_without_token_cannot_delete_protected_endpoints(journalist_app,
                                                              test_source):
    with journalist_app.app_context():
        protected_routes = [
            url_for('api.all_source_submissions',
                    source_id=test_source['source'].id),
            url_for('api.single_submission',
                    source_id=test_source['source'].id,
                    submission_id=test_source['submissions'][0].id),
            url_for('api.remove_star',
                    source_id=test_source['source'].id),
            ]

    with journalist_app.test_client() as app:
        for protected_route in protected_routes:
            response = app.delete(protected_route,
                               headers=get_api_headers(''))

            assert response.status_code == 403


def test_user_without_token_cannot_post_protected_endpoints(journalist_app,
                                                            test_source):
    with journalist_app.app_context():
        protected_routes = [
            url_for('api.post_reply', source_id=test_source['source'].id),
            url_for('api.add_star', source_id=test_source['source'].id)
        ]

    with journalist_app.test_client() as app:
        for protected_route in protected_routes:
            response = app.post(protected_route,
                                headers=get_api_headers(''))
            assert response.status_code == 403
