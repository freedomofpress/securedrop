"""
Basic smoke tests that verify the apps are functioning as expected
"""
import json

import pytest
import testutils

sdvars = testutils.securedrop_test_vars
testinfra_hosts = [sdvars.app_hostname]


@pytest.mark.parametrize(
    ("name", "url", "curl_flags", "expected"),
    [
        # We pass -L to follow the redirect from / to /login
        ("journalist", "http://localhost:8080/", "L", "Powered by"),
        ("source", "http://localhost:80/", "", "Powered by"),
        ("source", "http://localhost:80/public-key", "", "-----BEGIN PGP PUBLIC KEY BLOCK-----"),
    ],
)
def test_interface_up(host, name, url, curl_flags, expected):
    """
    Ensure the respective interface is up with HTTP 200 if not, we try our
    best to grab the error log and print it via an intentionally failed
    assertion.
    """
    response = host.run(f"curl -{curl_flags}i {url}").stdout
    if "200 OK" not in response:
        # Try to grab the log and print it via a failed assertion
        with host.sudo():
            f = host.file(f"/var/log/apache2/{name}-error.log")
            if f.exists:
                assert "nopenopenope" in f.content_string
    assert "200 OK" in response
    assert expected in response


def test_redwood(host):
    """
    Verify the redwood wheel was built and installed properly and basic
    functionality works
    """
    response = host.run(
        "/opt/venvs/securedrop-app-code/bin/python3 -c "
        "'import redwood; import json; print("
        'json.dumps(redwood.generate_source_key_pair("abcde", "test@invalid")))\''
    )
    parsed = json.loads(response.stdout)
    assert "-----BEGIN PGP PUBLIC KEY BLOCK-----" in parsed[0]
    assert "-----BEGIN PGP PRIVATE KEY BLOCK-----" in parsed[1]
    assert len(parsed[2]) == 40
