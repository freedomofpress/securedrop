import os
os.environ['SECUREDROP_ENV'] = 'test'
import json
import unittest

from flask import url_for
from flask_testing import TestCase

import journalist
import utils
from db import db_session, Journalist, Source, Reply, SourceStar, Submission


class TestJournalistAPITokenAuthentication(TestCase):
    def setUp(self):
        utils.env.setup()
        self.user, self.user_pw = utils.db_helper.init_journalist()

    def tearDown(self):
        utils.env.teardown()

    def create_app(self):
        return journalist.app

    def get_api_headers(self):
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def test_valid_user_can_get_an_api_token(self):
        valid_token = self.user.totp.now()
        response = self.client.post(url_for('api.get_token'),
                                    data=json.dumps({'username': self.user.username,
                                                     'password': self.user_pw,
                                                     'one_time_code': valid_token}),
                                    headers=self.get_api_headers())
        observed_response = json.loads(response.data)
        self.assertTrue(isinstance(Journalist.verify_api_token(observed_response['token']),
                                   Journalist)
                        )
        self.assertTrue(response.status_code == 200)

    def test_user_cannot_get_an_api_token_with_wrong_password(self):
        valid_token = self.user.totp.now()
        response = self.client.post(url_for('api.get_token'),
                                    data=json.dumps({'username': self.user.username,
                                                     'password': 'wrong password',
                                                     'one_time_code': valid_token}),
                                    headers=self.get_api_headers())
        observed_response = json.loads(response.data)
        self.assertTrue(response.status_code == 403)
        self.assertEqual(observed_response['error'], 'forbidden')

    def test_user_cannot_get_an_api_token_with_wrong_2fa_token(self):
        response = self.client.post(url_for('api.get_token'),
                                    data=json.dumps({'username': self.user.username,
                                                     'password': self.user_pw,
                                                     'one_time_code': '123456'}),
                                    headers=self.get_api_headers())
        observed_response = json.loads(response.data)
        self.assertTrue(response.status_code == 403)
        self.assertEqual(observed_response['error'], 'forbidden')


class TestJournalistAPI(TestCase):
    def get_api_token(self):
        valid_token = self.user.totp.now()
        response = self.client.post(url_for('api.get_token'),
                                    data=json.dumps({'username': self.user.username,
                                                     'password': self.user_pw,
                                                     'one_time_code': valid_token}),
                                    headers={'Accept': 'application/json',
                                             'Content-Type': 'application/json'})
        observed_response = json.loads(response.data)
        self.api_token = observed_response['token']

    def setUp(self):
        utils.env.setup()
        self.user, self.user_pw = utils.db_helper.init_journalist()
        self.get_api_token()

        # Add a test source and submissions
        self.source, _ = utils.db_helper.init_source()
        utils.db_helper.submit(self.source, 2)
        utils.db_helper.reply(self.user, self.source, 2)

    def tearDown(self):
        utils.env.teardown()

    def create_app(self):
        return journalist.app

    def get_api_headers(self, token):
        return {
            'Authorization': 'Token {}'.format(token),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def test_404(self):
        response = self.client.get(
            '/api/v1/notavalidurl',
            headers=self.get_api_headers(''))
        self.assertTrue(response.status_code == 404)
        json_response = json.loads(response.data)
        self.assertTrue(json_response['error'] == 'not found')

    def test_user_without_api_token_gets_all_endpoints(self):
        response = self.client.get(url_for('api.get_endpoints'),
                                   headers=self.get_api_headers(''))

        observed_endpoints = json.loads(response.data)

        for expected_endpoint in ['current_user_url', 'sources_url',
                                  'submissions_url']:
            self.assertIn(expected_endpoint, observed_endpoints.keys())

    def test_authorized_user_gets_all_sources(self):
        response = self.client.get(url_for('api.get_all_sources'),
                                   headers=self.get_api_headers(self.api_token))

        self.assertTrue(response.status_code == 200)

        data = json.loads(response.data)

        # We expect to see our source in the response
        self.assertEqual(self.source.journalist_designation,
                         data['sources'][0]['journalist_designation'])

    def test_user_without_api_token_cannot_http_get_protected_endpoints(self):
        for protected_route in [url_for('api.get_all_sources'),
                                url_for('api.single_source', source_id=self.source.id),
                                url_for('api.all_source_submissions', source_id=self.source.id),
                                url_for('api.get_current_user'),
                                url_for('api.get_all_submissions'),
                                url_for('api.get_current_user'),
                                url_for('api.single_submission', source_id=self.source.id,
                                        submission_id=self.source.submissions[0].id),
                                url_for('api.download_submission', source_id=self.source.id,
                                        submission_id=self.source.submissions[0].id)
                                ]:
            response = self.client.get(protected_route,
                                       headers=self.get_api_headers(''))

            self.assertTrue(response.status_code == 403)

    def test_user_without_api_token_cannot_http_delete_protected_endpoints(self):
        for protected_route in [url_for('api.all_source_submissions', source_id=self.source.id),
                                url_for('api.single_submission', source_id=self.source.id,
                                        submission_id=self.source.submissions[0].id),
                                url_for('api.remove_star', source_id=self.source.id)
                                ]:
            response = self.client.delete(protected_route,
                                          headers=self.get_api_headers(''))

            self.assertTrue(response.status_code == 403)

    def test_user_without_api_token_cannot_http_post_protected_endpoints(self):
        for protected_route in [url_for('api.post_reply', source_id=self.source.id),
                                url_for('api.add_star', source_id=self.source.id)]:
            response = self.client.post(protected_route,
                                        headers=self.get_api_headers(''))

            self.assertTrue(response.status_code == 403)

    def test_authorized_user_gets_single_source(self):
        response = self.client.get(url_for('api.single_source',
                                           source_id=self.source.id),
                                   headers=self.get_api_headers(self.api_token))

        self.assertTrue(response.status_code == 200)

    def test_get_non_existant_source_404s(self):
        not_a_valid_source_id = Source.query.count() + 1
        response = self.client.get(url_for('api.single_source',
                                           source_id=not_a_valid_source_id),
                                   headers=self.get_api_headers(self.api_token))

        self.assertTrue(response.status_code == 404)

    def test_get_non_existent_submission_404s(self):
        not_a_valid_submission_id = len(self.source.submissions) + 1
        response = self.client.get(url_for('api.single_submission',
                                           source_id=self.source.id,
                                           submission_id=not_a_valid_submission_id),
                                   headers=self.get_api_headers(self.api_token))

        self.assertTrue(response.status_code == 404)

    def test_authorized_user_can_get_single_submission(self):
        submission_id_to_get = self.source.submissions[0].id
        response = self.client.get(url_for('api.single_submission',
                                           source_id=self.source.id,
                                           submission_id=submission_id_to_get),
                                   headers=self.get_api_headers(self.api_token))

        self.assertTrue(response.status_code == 200)

        data = json.loads(response.data)

        self.assertEqual(data['submission_id'], submission_id_to_get)
        self.assertFalse(data['is_read'])
        self.assertEqual(data['filename'], self.source.submissions[0].filename)
        self.assertEqual(data['size'], self.source.submissions[0].size)

    def test_authorized_user_can_see_current_user_endpoint(self):
        response = self.client.get(url_for('api.get_current_user'),
                                   headers=self.get_api_headers(self.api_token))
        self.assertTrue(response.status_code == 200)

        data = json.loads(response.data)['user']

        self.assertFalse(data['is_admin'])
        self.assertEqual(data['username'], self.user.username)

    def test_authorized_user_can_see_all_submissions(self):
        response = self.client.get(url_for('api.all_source_submissions',
                                           source_id=self.source.id),
                                   headers=self.get_api_headers(self.api_token))
        self.assertTrue(response.status_code == 200)

        data = json.loads(response.data)

        observed_submissions = []
        for submission in data['submissions']:
            self.assertFalse(submission['is_read'])
            observed_submissions.append(submission['filename'])

        expected_submissions = [submission.filename for submission in self.source.submissions]
        self.assertEqual(observed_submissions, expected_submissions)

    def test_add_reply(self):
        response = self.client.post(url_for('api.post_reply', source_id=self.source.id),
                                   data=json.dumps({'reply': 'Hehehehe i am a unit test'}),
                                   headers=self.get_api_headers(self.api_token))

        # Get most recent reply
        reply = Reply.query.order_by(Reply.id.desc()).first()

        self.assertEqual(reply.journalist_id, self.user.id)
        self.assertEqual(reply.source_id, self.source.id)

    def test_source_starring_and_unstarring(self):
        response = self.client.post(url_for('api.add_star', source_id=self.source.id),
                                   headers=self.get_api_headers(self.api_token))

        # We expect the source to be starred now
        self.assertTrue(SourceStar.query.filter(SourceStar.source_id == self.source.id).one().starred)

        response = self.client.delete(url_for('api.remove_star', source_id=self.source.id),
                                   headers=self.get_api_headers(self.api_token))

        # And the star should now be gone
        self.assertFalse(SourceStar.query.filter(SourceStar.source_id == self.source.id).one().starred)

    def test_source_collection_deletion(self):
        response = self.client.delete(url_for('api.all_source_submissions', source_id=self.source.id),
                                      headers=self.get_api_headers(self.api_token))

        self.assertTrue(response.status_code == 200)

        # Source does not exist
        self.assertEqual(Source.query.all(), [])

    def test_single_submission_deletion(self):
        submission_id_to_delete = self.source.submissions[0].id
        response = self.client.delete(url_for('api.single_submission', source_id=self.source.id,
                                              submission_id=submission_id_to_delete),
                                      headers=self.get_api_headers(self.api_token))

        self.assertTrue(response.status_code == 200)

        # Submission should not exist
        self.assertEqual(Submission.query.filter(Submission.id == submission_id_to_delete).all(), [])

    def test_single_submission_download(self):
        submission_id_to_download = self.source.submissions[0].id

        response = self.client.get(url_for('api.download_submission', source_id=self.source.id,
                                           submission_id=submission_id_to_download),
                                      headers=self.get_api_headers(self.api_token))

        self.assertTrue(response.status_code == 200)

        # Submission should now be marked as downloaded
        submission = Submission.query.get(submission_id_to_download)
        self.assertTrue(submission.downloaded)

        # Response should be a PGP encrypted download
        self.assertEqual(response.mimetype, 'application/pgp-encrypted')
