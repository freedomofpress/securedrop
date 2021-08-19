# -*- coding: utf-8 -*-
import json
import os

import werkzeug

from source_app.utils import check_url_file, fit_codenames_into_cookie
from .test_journalist import VALID_PASSWORD


def test_check_url_file(config):

    assert check_url_file("nosuchfile", "whatever") is None

    try:
        def write_url_file(path, content):
            url_file = open(path, "w")
            url_file.write("{}\n".format(content))

        url_path = "test_source_url"

        onion_test_url = "abcdabcdabcdabcd.onion"
        write_url_file(url_path, onion_test_url)
        assert check_url_file(url_path, r"^[a-z0-9]{16}\.onion$") == onion_test_url

        onion_test_url = "abcdefghabcdefghabcdefghabcdefghabcdefghabcdefghabcdefgh.onion"
        write_url_file(url_path, onion_test_url)
        assert check_url_file(url_path, r"^[a-z0-9]{56}\.onion$") == onion_test_url

        write_url_file(url_path, "NO.onion")
        assert check_url_file(url_path, r"^[a-z0-9]{56}\.onion$") is None
    finally:
        if os.path.exists(url_path):
            os.unlink(url_path)


def test_fit_codenames_into_cookie(config):
    # A single codename should never be truncated.
    codenames = {'a': VALID_PASSWORD}
    assert(fit_codenames_into_cookie(codenames) == codenames)

    # A reasonable number of codenames should never be truncated.
    codenames = {
        'a': VALID_PASSWORD,
        'b': VALID_PASSWORD,
        'c': VALID_PASSWORD,
    }
    assert(fit_codenames_into_cookie(codenames) == codenames)

    # A single gargantuan codename is undefined behavior---but also should not
    # be truncated.
    codenames = {'a': werkzeug.Response.max_cookie_size*VALID_PASSWORD}
    assert(fit_codenames_into_cookie(codenames) == codenames)

    # Too many codenames of the expected length should be truncated.
    codenames = {}
    too_many = 2*(werkzeug.Response.max_cookie_size // len(VALID_PASSWORD))
    for i in range(too_many):
        codenames[i] = VALID_PASSWORD
    serialized = json.dumps(codenames).encode()
    assert(len(serialized) > werkzeug.Response.max_cookie_size)
    serialized = json.dumps(fit_codenames_into_cookie(codenames)).encode()
    assert(len(serialized) < werkzeug.Response.max_cookie_size)
