import os
os.environ['SECUREDROP_ENV'] = 'test'
import json
import unittest

from flask import url_for
from flask_testing import TestCase

import journalist
import utils


class TestJournalistAPI(TestCase):
    def setUp(self):
        utils.env.setup()

    def tearDown(self):
        utils.env.teardown()

    def create_app(self):
        return journalist.app

    def test_unauthenticated_user_gets_all_endpoints(self):
        response = self.client.get(url_for('api.get_endpoints'),
                                   content_type='application/json')

        observed_endpoints = json.loads(response.data)

        for expected_endpoint in ['current_user_url', 'sources_url',
                                  'submissions_url']:
            self.assertIn(expected_endpoint, observed_endpoints.keys())

    def test_authorized_user_gets_all_sources(self):
        # TODO: Authentication
        pass

    def test_authorized_user_gets_single_source(self):
        # TODO: Authentication
        pass
