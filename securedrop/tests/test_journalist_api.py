# -*- coding: utf-8 -*-
import json
import os
import pytest

from pyotp import TOTP

from flask import url_for

from models import Journalist, Source, SourceStar, Submission

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
            url_for('api.get_all_submissions')
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


def test_api_404(journalist_app, journalist_api_token):
    with journalist_app.test_client() as app:
        response = app.get('/api/v1/invalidendpoint',
                           headers=get_api_headers(journalist_api_token))
        json_response = json.loads(response.data)

        assert response.status_code == 404
        assert json_response['error'] == 'not found'


def test_authorized_user_gets_single_source(journalist_app, test_source,
                                            journalist_api_token):
    with journalist_app.test_client() as app:
        response = app.get(url_for('api.single_source',
                                   source_id=test_source['source'].id),
                           headers=get_api_headers(journalist_api_token))

        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['source_id'] == test_source['source'].id


def test_get_non_existant_source_404s(journalist_app, journalist_api_token):
    with journalist_app.test_client() as app:
        response = app.get(url_for('api.single_source',
                                   source_id=1),
                           headers=get_api_headers(journalist_api_token))

        assert response.status_code == 404


def test_authorized_user_can_star_a_source(journalist_app, test_source,
                                           journalist_api_token):
    with journalist_app.test_client() as app:
        source_id = test_source['source'].id
        response = app.post(url_for('api.add_star', source_id=source_id),
                            headers=get_api_headers(journalist_api_token))

        assert response.status_code == 201

        # Verify that the source was starred.
        assert SourceStar.query.filter(
            SourceStar.source_id == source_id).one().starred


def test_authorized_user_can_unstar_a_source(journalist_app, test_source,
                                             journalist_api_token):
    with journalist_app.test_client() as app:
        source_id = test_source['source'].id
        response = app.post(url_for('api.add_star', source_id=source_id),
                            headers=get_api_headers(journalist_api_token))
        assert response.status_code == 201

        response = app.delete(url_for('api.remove_star', source_id=source_id),
                              headers=get_api_headers(journalist_api_token))
        assert response.status_code == 200

        # Verify that the source is gone.
        assert SourceStar.query.filter(
            SourceStar.source_id == source_id).one().starred is False


def test_disallowed_methods_produces_405(journalist_app, test_source,
                                         journalist_api_token):
    with journalist_app.test_client() as app:
        source_id = test_source['source'].id
        response = app.delete(url_for('api.add_star', source_id=source_id),
                              headers=get_api_headers(journalist_api_token))
        json_response = json.loads(response.data)

        assert response.status_code == 405
        assert json_response['error'] == 'method not allowed'


def test_authorized_user_can_get_all_submissions(journalist_app, test_source,
                                                 journalist_api_token):
    with journalist_app.test_client() as app:
        response = app.get(url_for('api.get_all_submissions'),
                           headers=get_api_headers(journalist_api_token))
        assert response.status_code == 200

        json_response = json.loads(response.data)

        observed_submissions = [submission['filename'] for \
                                submission in json_response['submissions']]

        expected_submissions = [submission.filename for \
                                submission in Submission.query.all()]
        assert observed_submissions == expected_submissions


def test_authorized_user_get_source_submissions(journalist_app, test_source,
                                                journalist_api_token):
    with journalist_app.test_client() as app:
        source_id = test_source['source'].id
        response = app.get(url_for('api.all_source_submissions',
                                   source_id=source_id),
                           headers=get_api_headers(journalist_api_token))
        assert response.status_code == 200

        json_response = json.loads(response.data)

        observed_submissions = [submission['filename'] for \
                                submission in json_response['submissions']]

        expected_submissions = [submission.filename for submission in \
                                test_source['source'].submissions]
        assert observed_submissions == expected_submissions


def test_authorized_user_can_get_single_submission(journalist_app,
                                                   test_source,
                                                   journalist_api_token):
    with journalist_app.test_client() as app:
        submission_id = test_source['source'].submissions[0].id
        source_id = test_source['source'].id
        response = app.get(url_for('api.single_submission',
                                   source_id=source_id,
                                   submission_id=submission_id),
                           headers=get_api_headers(journalist_api_token))

        assert response.status_code == 200

        json_response = json.loads(response.data)

        assert json_response['submission_id'] == submission_id
        assert json_response['is_read'] is False
        assert json_response['filename'] == \
            test_source['source'].submissions[0].filename
        assert json_response['size'] == \
            test_source['source'].submissions[0].size


def test_authorized_user_can_delete_single_submission(journalist_app,
                                                      test_source,
                                                      journalist_api_token):
    with journalist_app.test_client() as app:
        submission_id = test_source['source'].submissions[0].id
        source_id = test_source['source'].id
        response = app.delete(url_for('api.single_submission',
                                      source_id=source_id,
                                      submission_id=submission_id),
                              headers=get_api_headers(journalist_api_token))

        assert response.status_code == 200

        # Submission now should be gone.
        assert Submission.query.filter(
            Submission.id == submission_id).all() == []


def test_authorized_user_can_delete_source_collection(journalist_app,
                                                      test_source,
                                                      journalist_api_token):
    with journalist_app.test_client() as app:
        submission_id = test_source['source'].submissions[0].id
        source_id = test_source['source'].id
        response = app.delete(url_for('api.all_source_submissions',
                                      source_id=source_id),
                              headers=get_api_headers(journalist_api_token))

        assert response.status_code == 200

        # Source does not exist
        assert Source.query.all() == []
