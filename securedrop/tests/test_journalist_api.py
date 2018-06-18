# -*- coding: utf-8 -*-
import json
import os
import pytest

from flask import url_for

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
from sdconfig import SDConfig, config


def test_unauthenticated_user_gets_all_endpoints(journalist_app):
    with journalist_app.test_client() as app:
        response = app.get(url_for('api.get_endpoints'),
                           content_type='application/json')

        observed_endpoints = json.loads(response.data)

        for expected_endpoint in ['current_user_url', 'sources_url',
                                  'submissions_url']:
            assert expected_endpoint in observed_endpoints.keys()
