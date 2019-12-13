# -*- coding: utf-8 -*-
import os

from source_app.utils import check_url_file


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
