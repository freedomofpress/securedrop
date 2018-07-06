# -*- coding: utf-8 -*-
import json
import os

from pyotp import TOTP

from flask import current_app, url_for

from models import Journalist, Reply, Source, SourceStar, Submission

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
from utils.api_helper import get_api_headers


def test_unauthenticated_user_gets_all_endpoints(journalist_app):
    with journalist_app.test_client() as app:
        response = app.get(url_for('api.get_endpoints'))

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
                                 'passphrase': test_journo['password'],
                                 'one_time_code': valid_token}),
                            headers=get_api_headers())
        observed_response = json.loads(response.data)

        assert isinstance(Journalist.validate_api_token_and_get_user(
            observed_response['token']), Journalist) is True
        assert response.status_code == 200


def test_user_cannot_get_an_api_token_with_wrong_password(journalist_app,
                                                          test_journo):
    with journalist_app.test_client() as app:
        valid_token = TOTP(test_journo['otp_secret']).now()
        response = app.post(url_for('api.get_token'),
                            data=json.dumps(
                                {'username': test_journo['username'],
                                 'passphrase': 'wrong password',
                                 'one_time_code': valid_token}),
                            headers=get_api_headers())
        observed_response = json.loads(response.data)

        assert response.status_code == 403
        assert observed_response['error'] == 'Forbidden'


def test_user_cannot_get_an_api_token_with_wrong_2fa_token(journalist_app,
                                                           test_journo):
    with journalist_app.test_client() as app:
        response = app.post(url_for('api.get_token'),
                            data=json.dumps(
                                {'username': test_journo['username'],
                                 'passphrase': test_journo['password'],
                                 'one_time_code': '123456'}),
                            headers=get_api_headers())
        observed_response = json.loads(response.data)

        assert response.status_code == 403
        assert observed_response['error'] == 'Forbidden'


def test_user_cannot_get_an_api_token_with_no_passphase_field(journalist_app,
                                                              test_journo):
    with journalist_app.test_client() as app:
        valid_token = TOTP(test_journo['otp_secret']).now()
        response = app.post(url_for('api.get_token'),
                            data=json.dumps(
                                {'username': test_journo['username'],
                                 'one_time_code': valid_token}),
                            headers=get_api_headers())
        observed_response = json.loads(response.data)

        assert response.status_code == 400
        assert observed_response['error'] == 'Bad Request'
        assert observed_response['message'] == 'passphrase field is missing'


def test_user_cannot_get_an_api_token_with_no_username_field(journalist_app,
                                                             test_journo):
    with journalist_app.test_client() as app:
        valid_token = TOTP(test_journo['otp_secret']).now()
        response = app.post(url_for('api.get_token'),
                            data=json.dumps(
                                {'passphrase': test_journo['password'],
                                 'one_time_code': valid_token}),
                            headers=get_api_headers())
        observed_response = json.loads(response.data)

        assert response.status_code == 400
        assert observed_response['error'] == 'Bad Request'
        assert observed_response['message'] == 'username field is missing'


def test_user_cannot_get_an_api_token_with_no_otp_field(journalist_app,
                                                        test_journo):
    with journalist_app.test_client() as app:
        response = app.post(url_for('api.get_token'),
                            data=json.dumps(
                                {'username': test_journo['username'],
                                 'passphrase': test_journo['password']}),
                            headers=get_api_headers())
        observed_response = json.loads(response.data)

        assert response.status_code == 400
        assert observed_response['error'] == 'Bad Request'
        assert observed_response['message'] == 'one_time_code field is missing'


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
        filesystem_id = test_source['source'].filesystem_id
        protected_routes = [
            url_for('api.get_all_sources'),
            url_for('api.single_source', filesystem_id=filesystem_id),
            url_for('api.all_source_submissions',
                    filesystem_id=filesystem_id),
            url_for('api.single_submission',
                    filesystem_id=filesystem_id,
                    submission_id=test_source['submissions'][0].id),
            url_for('api.download_submission',
                    filesystem_id=filesystem_id,
                    submission_id=test_source['submissions'][0].id),
            url_for('api.get_all_submissions'),
            url_for('api.get_current_user')
            ]

    with journalist_app.test_client() as app:
        for protected_route in protected_routes:
            response = app.get(protected_route,
                               headers=get_api_headers(''))

            assert response.status_code == 403


def test_user_without_token_cannot_delete_protected_endpoints(journalist_app,
                                                              test_source):
    with journalist_app.app_context():
        filesystem_id = test_source['source'].filesystem_id
        protected_routes = [
            url_for('api.single_source',
                    filesystem_id=filesystem_id),
            url_for('api.single_submission',
                    filesystem_id=filesystem_id,
                    submission_id=test_source['submissions'][0].id),
            url_for('api.remove_star',
                    filesystem_id=filesystem_id),
            ]

    with journalist_app.test_client() as app:
        for protected_route in protected_routes:
            response = app.delete(protected_route,
                                  headers=get_api_headers(''))

            assert response.status_code == 403


def test_user_without_token_cannot_post_protected_endpoints(journalist_app,
                                                            test_source):
    with journalist_app.app_context():
        filesystem_id = test_source['source'].filesystem_id
        protected_routes = [
            url_for('api.post_reply', filesystem_id=filesystem_id),
            url_for('api.add_star', filesystem_id=filesystem_id),
            url_for('api.flag', filesystem_id=filesystem_id)
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
        assert json_response['error'] == 'Not Found'


def test_authorized_user_gets_single_source(journalist_app, test_source,
                                            journalist_api_token):
    with journalist_app.test_client() as app:
        filesystem_id = test_source['source'].filesystem_id
        response = app.get(url_for('api.single_source',
                                   filesystem_id=filesystem_id),
                           headers=get_api_headers(journalist_api_token))

        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['source_id'] == test_source['source'].id
        assert 'BEGIN PGP PUBLIC KEY' in data['public_key']


def test_get_non_existant_source_404s(journalist_app, journalist_api_token):
    with journalist_app.test_client() as app:
        response = app.get(url_for('api.single_source',
                                   filesystem_id=1),
                           headers=get_api_headers(journalist_api_token))

        assert response.status_code == 404


def test_authorized_user_can_flag_a_source(journalist_app, test_source,
                                           journalist_api_token):
    with journalist_app.test_client() as app:
        filesystem_id = test_source['source'].filesystem_id
        source_id = test_source['source'].id
        response = app.post(url_for('api.flag',
                                    filesystem_id=filesystem_id),
                            headers=get_api_headers(journalist_api_token))

        assert response.status_code == 200

        # Verify that the source was flagged.
        assert Source.query.get(source_id).flagged


def test_authorized_user_can_star_a_source(journalist_app, test_source,
                                           journalist_api_token):
    with journalist_app.test_client() as app:
        filesystem_id = test_source['source'].filesystem_id
        source_id = test_source['source'].id
        response = app.post(url_for('api.add_star',
                                    filesystem_id=filesystem_id),
                            headers=get_api_headers(journalist_api_token))

        assert response.status_code == 201

        # Verify that the source was starred.
        assert SourceStar.query.filter(
            SourceStar.source_id == source_id).one().starred


def test_authorized_user_can_unstar_a_source(journalist_app, test_source,
                                             journalist_api_token):
    with journalist_app.test_client() as app:
        filesystem_id = test_source['source'].filesystem_id
        source_id = test_source['source'].id
        response = app.post(url_for('api.add_star',
                                    filesystem_id=filesystem_id),
                            headers=get_api_headers(journalist_api_token))
        assert response.status_code == 201

        response = app.delete(url_for('api.remove_star',
                                      filesystem_id=filesystem_id),
                              headers=get_api_headers(journalist_api_token))
        assert response.status_code == 200

        # Verify that the source is gone.
        assert SourceStar.query.filter(
            SourceStar.source_id == source_id).one().starred is False


def test_disallowed_methods_produces_405(journalist_app, test_source,
                                         journalist_api_token):
    with journalist_app.test_client() as app:
        filesystem_id = test_source['source'].filesystem_id
        response = app.delete(url_for('api.add_star',
                                      filesystem_id=filesystem_id),
                              headers=get_api_headers(journalist_api_token))
        json_response = json.loads(response.data)

        assert response.status_code == 405
        assert json_response['error'] == 'Method Not Allowed'


def test_authorized_user_can_get_all_submissions(journalist_app, test_source,
                                                 journalist_api_token):
    with journalist_app.test_client() as app:
        response = app.get(url_for('api.get_all_submissions'),
                           headers=get_api_headers(journalist_api_token))
        assert response.status_code == 200

        json_response = json.loads(response.data)

        observed_submissions = [submission['filename'] for
                                submission in json_response['submissions']]

        expected_submissions = [submission.filename for
                                submission in Submission.query.all()]
        assert observed_submissions == expected_submissions


def test_authorized_user_get_source_submissions(journalist_app, test_source,
                                                journalist_api_token):
    with journalist_app.test_client() as app:
        filesystem_id = test_source['source'].filesystem_id
        response = app.get(url_for('api.all_source_submissions',
                                   filesystem_id=filesystem_id),
                           headers=get_api_headers(journalist_api_token))
        assert response.status_code == 200

        json_response = json.loads(response.data)

        observed_submissions = [submission['filename'] for
                                submission in json_response['submissions']]

        expected_submissions = [submission.filename for submission in
                                test_source['source'].submissions]
        assert observed_submissions == expected_submissions


def test_authorized_user_can_get_single_submission(journalist_app,
                                                   test_source,
                                                   journalist_api_token):
    with journalist_app.test_client() as app:
        submission_id = test_source['source'].submissions[0].id
        filesystem_id = test_source['source'].filesystem_id
        response = app.get(url_for('api.single_submission',
                                   filesystem_id=filesystem_id,
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
        filesystem_id = test_source['source'].filesystem_id
        response = app.delete(url_for('api.single_submission',
                                      filesystem_id=filesystem_id,
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
        filesystem_id = test_source['source'].filesystem_id
        response = app.delete(url_for('api.single_source',
                                      filesystem_id=filesystem_id),
                              headers=get_api_headers(journalist_api_token))

        assert response.status_code == 200

        # Source does not exist
        assert Source.query.all() == []


def test_authorized_user_can_download_submission(journalist_app,
                                                 test_source,
                                                 journalist_api_token):
    with journalist_app.test_client() as app:
        submission_id = test_source['source'].submissions[0].id
        filesystem_id = test_source['source'].filesystem_id

        response = app.get(url_for('api.download_submission',
                                   filesystem_id=filesystem_id,
                                   submission_id=submission_id),
                           headers=get_api_headers(journalist_api_token))

        assert response.status_code == 200

        # Submission should now be marked as downloaded in the database
        submission = Submission.query.get(submission_id)
        assert submission.downloaded

        # Response should be a PGP encrypted download
        assert response.mimetype == 'application/pgp-encrypted'


def test_authorized_user_can_get_current_user_endpoint(journalist_app,
                                                       test_source,
                                                       test_journo,
                                                       journalist_api_token):
    with journalist_app.test_client() as app:
        response = app.get(url_for('api.get_current_user'),
                           headers=get_api_headers(journalist_api_token))
        assert response.status_code == 200

        json_response = json.loads(response.data)
        assert json_response['is_admin'] is False
        assert json_response['username'] == test_journo['username']


def test_request_with_missing_auth_header_triggers_403(journalist_app):
    with journalist_app.test_client() as app:
        response = app.get(url_for('api.get_current_user'),
                           headers={
                               'Accept': 'application/json',
                               'Content-Type': 'application/json'
                           })
        assert response.status_code == 403


def test_request_with_auth_header_but_no_token_triggers_403(journalist_app):
    with journalist_app.test_client() as app:
        response = app.get(url_for('api.get_current_user'),
                           headers={
                               'Authorization': '',
                               'Accept': 'application/json',
                               'Content-Type': 'application/json'
                           })
        assert response.status_code == 403


def test_unencrypted_replies_get_rejected(journalist_app, journalist_api_token,
                                          test_source, test_journo):
    with journalist_app.test_client() as app:
        filesystem_id = test_source['source'].filesystem_id
        reply_content = 'This is a plaintext reply'
        response = app.post(url_for('api.post_reply',
                                    filesystem_id=filesystem_id),
                            data=json.dumps({'reply': reply_content}),
                            headers=get_api_headers(journalist_api_token))
        assert response.status_code == 400


def test_authorized_user_can_add_reply(journalist_app, journalist_api_token,
                                       test_source, test_journo):
    with journalist_app.test_client() as app:
        source_id = test_source['source'].id
        filesystem_id = test_source['source'].filesystem_id

        # First we must encrypt the reply, or it will get rejected
        # by the server.
        source_key = current_app.crypto_util.getkey(
            test_source['source'].filesystem_id)
        reply_content = current_app.crypto_util.gpg.encrypt(
            'This is a plaintext reply', source_key).data

        response = app.post(url_for('api.post_reply',
                                    filesystem_id=filesystem_id),
                            data=json.dumps({'reply': reply_content}),
                            headers=get_api_headers(journalist_api_token))
        assert response.status_code == 201

    with journalist_app.app_context():  # Now verify everything was saved.
        # Get most recent reply in the database
        reply = Reply.query.order_by(Reply.id.desc()).first()

        assert reply.journalist_id == test_journo['id']
        assert reply.source_id == source_id

        source = Source.query.get(source_id)

        expected_filename = '{}-{}-reply.gpg'.format(
            source.interaction_count, source.journalist_filename)

        expected_filepath = current_app.storage.path(
            source.filesystem_id, expected_filename)

        with open(expected_filepath, 'rb') as fh:
            saved_content = fh.read()

        assert reply_content == saved_content


def test_reply_without_content_400(journalist_app, journalist_api_token,
                                   test_source, test_journo):
    with journalist_app.test_client() as app:
        filesystem_id = test_source['source'].filesystem_id
        response = app.post(url_for('api.post_reply',
                                    filesystem_id=filesystem_id),
                            data=json.dumps({'reply': ''}),
                            headers=get_api_headers(journalist_api_token))
        assert response.status_code == 400


def test_reply_without_reply_field_400(journalist_app, journalist_api_token,
                                       test_source, test_journo):
    with journalist_app.test_client() as app:
        filesystem_id = test_source['source'].filesystem_id
        response = app.post(url_for('api.post_reply',
                                    filesystem_id=filesystem_id),
                            data=json.dumps({'other': 'stuff'}),
                            headers=get_api_headers(journalist_api_token))
        assert response.status_code == 400


def test_reply_without_json_400(journalist_app, journalist_api_token,
                                test_source, test_journo):
    with journalist_app.test_client() as app:
        filesystem_id = test_source['source'].filesystem_id
        response = app.post(url_for('api.post_reply',
                                    filesystem_id=filesystem_id),
                            data='invalid',
                            headers=get_api_headers(journalist_api_token))
        assert response.status_code == 400


def test_reply_with_valid_curly_json_400(journalist_app, journalist_api_token,
                                         test_source, test_journo):
    with journalist_app.test_client() as app:
        filesystem_id = test_source['source'].filesystem_id
        response = app.post(url_for('api.post_reply',
                                    filesystem_id=filesystem_id),
                            data='{}',
                            headers=get_api_headers(journalist_api_token))
        assert response.status_code == 400

        json_response = json.loads(response.data)
        assert json_response['message'] == 'reply not found in request body'


def test_reply_with_valid_square_json_400(journalist_app, journalist_api_token,
                                          test_source, test_journo):
    with journalist_app.test_client() as app:
        filesystem_id = test_source['source'].filesystem_id
        response = app.post(url_for('api.post_reply',
                                    filesystem_id=filesystem_id),
                            data='[]',
                            headers=get_api_headers(journalist_api_token))
        assert response.status_code == 400

        json_response = json.loads(response.data)
        assert json_response['message'] == 'reply not found in request body'
