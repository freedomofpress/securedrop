# -*- coding: utf-8 -*-
import hashlib
import json
import os
import random

from pyotp import TOTP
from uuid import UUID, uuid4

from flask import current_app, url_for
from itsdangerous import TimedJSONWebSignatureSerializer

from db import db
from models import Journalist, Reply, Source, SourceStar, Submission

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
from utils.api_helper import get_api_headers

random.seed('◔ ⌣ ◔')


def test_unauthenticated_user_gets_all_endpoints(journalist_app):
    with journalist_app.test_client() as app:
        response = app.get(url_for('api.get_endpoints'))

        observed_endpoints = json.loads(response.data)
        expected_endpoints = [u'current_user_url', u'submissions_url',
                              u'sources_url', u'auth_token_url',
                              u'replies_url']
        assert expected_endpoints == observed_endpoints.keys()


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

        assert observed_response['journalist_uuid'] == test_journo['uuid']
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
                                                           test_journo,
                                                           hardening):
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


def test_authorized_user_gets_all_sources(journalist_app, test_submissions,
                                          journalist_api_token):
    with journalist_app.test_client() as app:
        response = app.get(url_for('api.get_all_sources'),
                           headers=get_api_headers(journalist_api_token))

        data = json.loads(response.data)

        assert response.status_code == 200

        # We expect to see our test source in the response
        assert test_submissions['source'].journalist_designation == \
            data['sources'][0]['journalist_designation']


def test_user_without_token_cannot_get_protected_endpoints(journalist_app,
                                                           test_files):
    with journalist_app.app_context():
        uuid = test_files['source'].uuid
        protected_routes = [
            url_for('api.get_all_sources'),
            url_for('api.single_source', source_uuid=uuid),
            url_for('api.all_source_submissions', source_uuid=uuid),
            url_for('api.single_submission', source_uuid=uuid,
                    submission_uuid=test_files['submissions'][0].uuid),
            url_for('api.download_submission', source_uuid=uuid,
                    submission_uuid=test_files['submissions'][0].uuid),
            url_for('api.get_all_submissions'),
            url_for('api.get_all_replies'),
            url_for('api.single_reply', source_uuid=uuid,
                    reply_uuid=test_files['replies'][0].uuid),
            url_for('api.all_source_replies', source_uuid=uuid),
            url_for('api.get_current_user')
            ]

    with journalist_app.test_client() as app:
        for protected_route in protected_routes:
            response = app.get(protected_route,
                               headers=get_api_headers(''))

            assert response.status_code == 403


def test_user_without_token_cannot_del_protected_endpoints(journalist_app,
                                                           test_submissions):
    with journalist_app.app_context():
        uuid = test_submissions['source'].uuid
        protected_routes = [
            url_for('api.single_source', source_uuid=uuid),
            url_for('api.single_submission', source_uuid=uuid,
                    submission_uuid=test_submissions['submissions'][0].uuid),
            url_for('api.remove_star', source_uuid=uuid),
            ]

    with journalist_app.test_client() as app:
        for protected_route in protected_routes:
            response = app.delete(protected_route,
                                  headers=get_api_headers(''))

            assert response.status_code == 403


def test_attacker_cannot_create_valid_token_with_none_alg(journalist_app,
                                                          test_source,
                                                          test_journo):
    with journalist_app.test_client() as app:
        uuid = test_source['source'].uuid
        s = TimedJSONWebSignatureSerializer('not the secret key',
                                            algorithm_name='none')
        attacker_token = s.dumps({'id': test_journo['id']}).decode('ascii')

        response = app.delete(url_for('api.single_source', source_uuid=uuid),
                              headers=get_api_headers(attacker_token))

        assert response.status_code == 403


def test_attacker_cannot_use_token_after_admin_deletes(journalist_app,
                                                       test_source,
                                                       journalist_api_token):

    with journalist_app.test_client() as app:
        uuid = test_source['source'].uuid

        # In a scenario where an attacker compromises a journalist workstation
        # the admin should be able to delete the user and their token should
        # no longer be valid.
        attacker = Journalist.validate_api_token_and_get_user(
            journalist_api_token)

        db.session.delete(attacker)
        db.session.commit()

        # Now this token should not be valid.
        response = app.delete(url_for('api.single_source', source_uuid=uuid),
                              headers=get_api_headers(journalist_api_token))

        assert response.status_code == 403


def test_user_without_token_cannot_post_protected_endpoints(journalist_app,
                                                            test_source):
    with journalist_app.app_context():
        uuid = test_source['source'].uuid
        protected_routes = [
            url_for('api.all_source_replies', source_uuid=uuid),
            url_for('api.add_star', source_uuid=uuid),
            url_for('api.flag', source_uuid=uuid)
        ]

    with journalist_app.test_client() as app:
        for protected_route in protected_routes:
            response = app.post(protected_route,
                                headers=get_api_headers(''),
                                data=json.dumps({'some': 'stuff'}))
            assert response.status_code == 403


def test_api_404(journalist_app, journalist_api_token):
    with journalist_app.test_client() as app:
        response = app.get('/api/v1/invalidendpoint',
                           headers=get_api_headers(journalist_api_token))
        json_response = json.loads(response.data)

        assert response.status_code == 404
        assert json_response['error'] == 'Not Found'


def test_trailing_slash_cleanly_404s(journalist_app, test_source,
                                     journalist_api_token):
    with journalist_app.test_client() as app:
        uuid = test_source['source'].uuid
        response = app.get(url_for('api.single_source',
                                   source_uuid=uuid) + '/',
                           headers=get_api_headers(journalist_api_token))
        json_response = json.loads(response.data)

        assert response.status_code == 404
        assert json_response['error'] == 'Not Found'


def test_authorized_user_gets_single_source(journalist_app, test_source,
                                            journalist_api_token):
    with journalist_app.test_client() as app:
        uuid = test_source['source'].uuid
        response = app.get(url_for('api.single_source', source_uuid=uuid),
                           headers=get_api_headers(journalist_api_token))

        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['uuid'] == test_source['source'].uuid
        assert 'BEGIN PGP PUBLIC KEY' in data['key']['public']


def test_get_non_existant_source_404s(journalist_app, journalist_api_token):
    with journalist_app.test_client() as app:
        response = app.get(url_for('api.single_source', source_uuid=1),
                           headers=get_api_headers(journalist_api_token))

        assert response.status_code == 404


def test_authorized_user_can_flag_a_source(journalist_app, test_source,
                                           journalist_api_token):
    with journalist_app.test_client() as app:
        uuid = test_source['source'].uuid
        source_id = test_source['source'].id
        response = app.post(url_for('api.flag', source_uuid=uuid),
                            headers=get_api_headers(journalist_api_token))

        assert response.status_code == 200

        # Verify that the source was flagged.
        assert Source.query.get(source_id).flagged


def test_authorized_user_can_star_a_source(journalist_app, test_source,
                                           journalist_api_token):
    with journalist_app.test_client() as app:
        uuid = test_source['source'].uuid
        source_id = test_source['source'].id
        response = app.post(url_for('api.add_star', source_uuid=uuid),
                            headers=get_api_headers(journalist_api_token))

        assert response.status_code == 201

        # Verify that the source was starred.
        assert SourceStar.query.filter(
            SourceStar.source_id == source_id).one().starred

        # API should also report is_starred is true
        response = app.get(url_for('api.single_source', source_uuid=uuid),
                           headers=get_api_headers(journalist_api_token))
        json_response = json.loads(response.data)
        assert json_response['is_starred'] is True


def test_authorized_user_can_unstar_a_source(journalist_app, test_source,
                                             journalist_api_token):
    with journalist_app.test_client() as app:
        uuid = test_source['source'].uuid
        source_id = test_source['source'].id
        response = app.post(url_for('api.add_star', source_uuid=uuid),
                            headers=get_api_headers(journalist_api_token))
        assert response.status_code == 201

        response = app.delete(url_for('api.remove_star', source_uuid=uuid),
                              headers=get_api_headers(journalist_api_token))
        assert response.status_code == 200

        # Verify that the source is gone.
        assert SourceStar.query.filter(
            SourceStar.source_id == source_id).one().starred is False

        # API should also report is_starred is false
        response = app.get(url_for('api.single_source', source_uuid=uuid),
                           headers=get_api_headers(journalist_api_token))
        json_response = json.loads(response.data)
        assert json_response['is_starred'] is False


def test_disallowed_methods_produces_405(journalist_app, test_source,
                                         journalist_api_token):
    with journalist_app.test_client() as app:
        uuid = test_source['source'].uuid
        response = app.delete(url_for('api.add_star', source_uuid=uuid),
                              headers=get_api_headers(journalist_api_token))
        json_response = json.loads(response.data)

        assert response.status_code == 405
        assert json_response['error'] == 'Method Not Allowed'


def test_authorized_user_can_get_all_submissions(journalist_app,
                                                 test_submissions,
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


def test_authorized_user_get_source_submissions(journalist_app,
                                                test_submissions,
                                                journalist_api_token):
    with journalist_app.test_client() as app:
        uuid = test_submissions['source'].uuid
        response = app.get(url_for('api.all_source_submissions',
                                   source_uuid=uuid),
                           headers=get_api_headers(journalist_api_token))
        assert response.status_code == 200

        json_response = json.loads(response.data)

        observed_submissions = [submission['filename'] for
                                submission in json_response['submissions']]

        expected_submissions = [submission.filename for submission in
                                test_submissions['source'].submissions]
        assert observed_submissions == expected_submissions


def test_authorized_user_can_get_single_submission(journalist_app,
                                                   test_submissions,
                                                   journalist_api_token):
    with journalist_app.test_client() as app:
        submission_uuid = test_submissions['source'].submissions[0].uuid
        uuid = test_submissions['source'].uuid
        response = app.get(url_for('api.single_submission',
                                   source_uuid=uuid,
                                   submission_uuid=submission_uuid),
                           headers=get_api_headers(journalist_api_token))

        assert response.status_code == 200

        json_response = json.loads(response.data)

        assert json_response['uuid'] == submission_uuid
        assert json_response['is_read'] is False
        assert json_response['filename'] == \
            test_submissions['source'].submissions[0].filename
        assert json_response['size'] == \
            test_submissions['source'].submissions[0].size


def test_authorized_user_can_get_all_replies(journalist_app, test_files,
                                             journalist_api_token):
    with journalist_app.test_client() as app:
        response = app.get(url_for('api.get_all_replies'),
                           headers=get_api_headers(journalist_api_token))
        assert response.status_code == 200

        json_response = json.loads(response.data)

        observed_replies = [reply['filename'] for
                            reply in json_response['replies']]

        expected_replies = [reply.filename for
                            reply in Reply.query.all()]
        assert observed_replies == expected_replies


def test_authorized_user_get_source_replies(journalist_app, test_files,
                                            journalist_api_token):
    with journalist_app.test_client() as app:
        uuid = test_files['source'].uuid
        response = app.get(url_for('api.all_source_replies',
                                   source_uuid=uuid),
                           headers=get_api_headers(journalist_api_token))
        assert response.status_code == 200

        json_response = json.loads(response.data)

        observed_replies = [reply['filename'] for
                            reply in json_response['replies']]

        expected_replies = [reply.filename for
                            reply in test_files['source'].replies]
        assert observed_replies == expected_replies


def test_authorized_user_can_get_single_reply(journalist_app, test_files,
                                              journalist_api_token):
    with journalist_app.test_client() as app:
        reply_uuid = test_files['source'].replies[0].uuid
        uuid = test_files['source'].uuid
        response = app.get(url_for('api.single_reply',
                                   source_uuid=uuid,
                                   reply_uuid=reply_uuid),
                           headers=get_api_headers(journalist_api_token))

        assert response.status_code == 200

        json_response = json.loads(response.data)

        reply = Reply.query.filter(Reply.uuid == reply_uuid).one()

        assert json_response['uuid'] == reply_uuid
        assert json_response['journalist_username'] == \
            reply.journalist.username
        assert json_response['journalist_uuid'] == \
            reply.journalist.uuid
        assert json_response['is_deleted_by_source'] is False
        assert json_response['filename'] == \
            test_files['source'].replies[0].filename
        assert json_response['size'] == \
            test_files['source'].replies[0].size


def test_authorized_user_can_delete_single_submission(journalist_app,
                                                      test_submissions,
                                                      journalist_api_token):
    with journalist_app.test_client() as app:
        submission_uuid = test_submissions['source'].submissions[0].uuid
        uuid = test_submissions['source'].uuid
        response = app.delete(url_for('api.single_submission',
                                      source_uuid=uuid,
                                      submission_uuid=submission_uuid),
                              headers=get_api_headers(journalist_api_token))

        assert response.status_code == 200

        # Submission now should be gone.
        assert Submission.query.filter(
            Submission.uuid == submission_uuid).all() == []


def test_authorized_user_can_delete_single_reply(journalist_app, test_files,
                                                 journalist_api_token):
    with journalist_app.test_client() as app:
        reply_uuid = test_files['source'].replies[0].uuid
        uuid = test_files['source'].uuid
        response = app.delete(url_for('api.single_reply',
                                      source_uuid=uuid,
                                      reply_uuid=reply_uuid),
                              headers=get_api_headers(journalist_api_token))

        assert response.status_code == 200

        # Reply should now be gone.
        assert Reply.query.filter(Reply.uuid == reply_uuid).all() == []


def test_authorized_user_can_delete_source_collection(journalist_app,
                                                      test_source,
                                                      journalist_api_token):
    with journalist_app.test_client() as app:
        uuid = test_source['source'].uuid
        response = app.delete(url_for('api.single_source', source_uuid=uuid),
                              headers=get_api_headers(journalist_api_token))

        assert response.status_code == 200

        # Source does not exist
        assert Source.query.all() == []


def test_authorized_user_can_download_submission(journalist_app,
                                                 test_submissions,
                                                 journalist_api_token):
    with journalist_app.test_client() as app:
        submission_uuid = test_submissions['source'].submissions[0].uuid
        uuid = test_submissions['source'].uuid

        response = app.get(url_for('api.download_submission',
                                   source_uuid=uuid,
                                   submission_uuid=submission_uuid),
                           headers=get_api_headers(journalist_api_token))

        assert response.status_code == 200

        # Submission should now be marked as downloaded in the database
        submission = Submission.query.get(
            test_submissions['source'].submissions[0].id)
        assert submission.downloaded

        # Response should be a PGP encrypted download
        assert response.mimetype == 'application/pgp-encrypted'

        # Response should have Etag field with hash
        assert response.headers['ETag'] == '"sha256:{}"'.format(
            hashlib.sha256(response.data).hexdigest())


def test_authorized_user_can_download_reply(journalist_app, test_files,
                                            journalist_api_token):
    with journalist_app.test_client() as app:
        reply_uuid = test_files['source'].replies[0].uuid
        uuid = test_files['source'].uuid

        response = app.get(url_for('api.download_reply',
                                   source_uuid=uuid,
                                   reply_uuid=reply_uuid),
                           headers=get_api_headers(journalist_api_token))

        assert response.status_code == 200

        # Response should be a PGP encrypted download
        assert response.mimetype == 'application/pgp-encrypted'

        # Response should have Etag field with hash
        assert response.headers['ETag'] == '"sha256:{}"'.format(
            hashlib.sha256(response.data).hexdigest())


def test_authorized_user_can_get_current_user_endpoint(journalist_app,
                                                       test_journo,
                                                       journalist_api_token):
    with journalist_app.test_client() as app:
        response = app.get(url_for('api.get_current_user'),
                           headers=get_api_headers(journalist_api_token))
        assert response.status_code == 200

        json_response = json.loads(response.data)
        assert json_response['is_admin'] is False
        assert json_response['username'] == test_journo['username']
        assert json_response['uuid'] == test_journo['journalist'].uuid


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
        uuid = test_source['source'].uuid
        reply_content = 'This is a plaintext reply'
        response = app.post(url_for('api.all_source_replies',
                                    source_uuid=uuid),
                            data=json.dumps({'reply': reply_content}),
                            headers=get_api_headers(journalist_api_token))
        assert response.status_code == 400


def test_authorized_user_can_add_reply(journalist_app, journalist_api_token,
                                       test_source, test_journo):
    with journalist_app.test_client() as app:
        source_id = test_source['source'].id
        uuid = test_source['source'].uuid

        # First we must encrypt the reply, or it will get rejected
        # by the server.
        source_key = current_app.crypto_util.getkey(
            test_source['source'].filesystem_id)
        reply_content = current_app.crypto_util.gpg.encrypt(
            'This is a plaintext reply', source_key).data

        response = app.post(url_for('api.all_source_replies',
                                    source_uuid=uuid),
                            data=json.dumps({'reply': reply_content}),
                            headers=get_api_headers(journalist_api_token))
        assert response.status_code == 201

    # ensure the uuid is present and valid
    reply_uuid = UUID(response.json['uuid'])

    # check that the uuid has a matching db object
    reply = Reply.query.filter_by(uuid=str(reply_uuid)).one_or_none()
    assert reply is not None

    # check that the filename is present and correct (#4047)
    assert response.json['filename'] == reply.filename

    with journalist_app.app_context():  # Now verify everything was saved.
        assert reply.journalist_id == test_journo['id']
        assert reply.source_id == source_id

        # regression test for #3918
        assert '/' not in reply.filename

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
        uuid = test_source['source'].uuid
        response = app.post(url_for('api.all_source_replies',
                                    source_uuid=uuid),
                            data=json.dumps({'reply': ''}),
                            headers=get_api_headers(journalist_api_token))
        assert response.status_code == 400


def test_reply_without_reply_field_400(journalist_app, journalist_api_token,
                                       test_source, test_journo):
    with journalist_app.test_client() as app:
        uuid = test_source['source'].uuid
        response = app.post(url_for('api.all_source_replies',
                                    source_uuid=uuid),
                            data=json.dumps({'other': 'stuff'}),
                            headers=get_api_headers(journalist_api_token))
        assert response.status_code == 400


def test_reply_without_json_400(journalist_app, journalist_api_token,
                                test_source, test_journo):
    with journalist_app.test_client() as app:
        uuid = test_source['source'].uuid
        response = app.post(url_for('api.all_source_replies',
                                    source_uuid=uuid),
                            data='invalid',
                            headers=get_api_headers(journalist_api_token))
        assert response.status_code == 400


def test_reply_with_valid_curly_json_400(journalist_app, journalist_api_token,
                                         test_source, test_journo):
    with journalist_app.test_client() as app:
        uuid = test_source['source'].uuid
        response = app.post(url_for('api.all_source_replies',
                                    source_uuid=uuid),
                            data='{}',
                            headers=get_api_headers(journalist_api_token))
        assert response.status_code == 400

        json_response = json.loads(response.data)
        assert json_response['message'] == 'reply not found in request body'


def test_reply_with_valid_square_json_400(journalist_app, journalist_api_token,
                                          test_source, test_journo):
    with journalist_app.test_client() as app:
        uuid = test_source['source'].uuid
        response = app.post(url_for('api.all_source_replies',
                                    source_uuid=uuid),
                            data='[]',
                            headers=get_api_headers(journalist_api_token))
        assert response.status_code == 400

        json_response = json.loads(response.data)
        assert json_response['message'] == 'reply not found in request body'


def test_malformed_json_400(journalist_app, journalist_api_token, test_journo,
                            test_source):

    with journalist_app.app_context():
        uuid = test_source['source'].uuid
        protected_routes = [
            url_for('api.get_token'),
            url_for('api.all_source_replies', source_uuid=uuid),
            url_for('api.add_star', source_uuid=uuid),
            url_for('api.flag', source_uuid=uuid),
        ]
    with journalist_app.test_client() as app:
        for protected_route in protected_routes:

            response = app.post(protected_route,
                                data="{this is invalid {json!",
                                headers=get_api_headers(journalist_api_token))
            observed_response = json.loads(response.data)

            assert response.status_code == 400
            assert observed_response['error'] == 'Bad Request'


def test_empty_json_400(journalist_app, journalist_api_token, test_journo,
                        test_source):

    with journalist_app.app_context():
        uuid = test_source['source'].uuid
        protected_routes = [
            url_for('api.get_token'),
            url_for('api.all_source_replies', source_uuid=uuid),
        ]
    with journalist_app.test_client() as app:
        for protected_route in protected_routes:

            response = app.post(protected_route,
                                data="",
                                headers=get_api_headers(journalist_api_token))
            observed_response = json.loads(response.data)

            assert response.status_code == 400
            assert observed_response['error'] == 'Bad Request'


def test_empty_json_20X(journalist_app, journalist_api_token, test_journo,
                        test_source):

    with journalist_app.app_context():
        uuid = test_source['source'].uuid
        protected_routes = [
            url_for('api.add_star', source_uuid=uuid),
            url_for('api.flag', source_uuid=uuid),
        ]
    with journalist_app.test_client() as app:
        for protected_route in protected_routes:

            response = app.post(protected_route,
                                data="",
                                headers=get_api_headers(journalist_api_token))

            assert response.status_code in (200, 201)


def test_set_reply_uuid(journalist_app, journalist_api_token, test_source):
    msg = '-----BEGIN PGP MESSAGE-----\nwat\n-----END PGP MESSAGE-----'
    reply_uuid = str(uuid4())
    req_data = {'uuid': reply_uuid, 'reply': msg}

    with journalist_app.test_client() as app:
        # first check that we can set a valid UUID
        source_uuid = test_source['uuid']
        resp = app.post(url_for('api.all_source_replies',
                                source_uuid=source_uuid),
                        data=json.dumps(req_data),
                        headers=get_api_headers(journalist_api_token))
        assert resp.status_code == 201
        assert resp.json['uuid'] == reply_uuid

        reply = Reply.query.filter_by(uuid=reply_uuid).one_or_none()
        assert reply is not None

        len_of_replies = len(Source.query.get(test_source['id']).replies)

        # next check that requesting with the same UUID does not succeed
        source_uuid = test_source['uuid']
        resp = app.post(url_for('api.all_source_replies',
                                source_uuid=source_uuid),
                        data=json.dumps(req_data),
                        headers=get_api_headers(journalist_api_token))
        assert resp.status_code == 409

        new_len_of_replies = len(Source.query.get(test_source['id']).replies)

        assert new_len_of_replies == len_of_replies

        # check setting null for the uuid field doesn't break
        req_data['uuid'] = None
        source_uuid = test_source['uuid']
        resp = app.post(url_for('api.all_source_replies',
                                source_uuid=source_uuid),
                        data=json.dumps(req_data),
                        headers=get_api_headers(journalist_api_token))
        assert resp.status_code == 201

        new_uuid = resp.json['uuid']
        reply = Reply.query.filter_by(uuid=new_uuid).one_or_none()
        assert reply is not None

        # check setting invalid values for the uuid field doesn't break
        req_data['uuid'] = 'not a uuid'
        source_uuid = test_source['uuid']
        resp = app.post(url_for('api.all_source_replies',
                                source_uuid=source_uuid),
                        data=json.dumps(req_data),
                        headers=get_api_headers(journalist_api_token))
        assert resp.status_code == 400


def test_api_does_not_set_cookie_headers(journalist_app, test_journo):
    with journalist_app.test_client() as app:
        response = app.get(url_for('api.get_endpoints'))

        observed_headers = response.headers
        assert 'Set-Cookie' not in observed_headers.keys()
        if 'Vary' in observed_headers.keys():
            assert 'Cookie' not in observed_headers['Vary']


# regression test for #4053
def test_malformed_auth_token(journalist_app, journalist_api_token):
    with journalist_app.app_context():
        # we know this endpoint requires an auth header
        url = url_for('api.get_all_sources')

    with journalist_app.test_client() as app:
        # precondition to ensure token is even valid
        resp = app.get(url, headers={'Authorization': 'Token {}'.format(journalist_api_token)})
        assert resp.status_code == 200

        resp = app.get(url, headers={'Authorization': 'not-token {}'.format(journalist_api_token)})
        assert resp.status_code == 403

        resp = app.get(url, headers={'Authorization': journalist_api_token})
        assert resp.status_code == 403

        resp = app.get(url, headers={'Authorization': 'too many {}'.format(journalist_api_token)})
        assert resp.status_code == 403
