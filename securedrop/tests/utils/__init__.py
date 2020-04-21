# -*- coding: utf-8 -*-

from flask import g
from pyotp import TOTP

from . import asynchronous  # noqa
from . import db_helper  # noqa
from . import env  # noqa


def login_user(app, test_user):
    resp = app.post('/login',
                    data={'username': test_user['username'],
                          'password': test_user['password'],
                          'token': TOTP(test_user['otp_secret']).now()},
                    follow_redirects=True)
    assert resp.status_code == 200
    assert hasattr(g, 'user')  # ensure logged in
