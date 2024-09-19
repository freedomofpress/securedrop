"""
Basic smoke tests that verify the apps are functioning as expected
"""

import json
from pathlib import Path

import pytest
import testutils

sdvars = testutils.securedrop_test_vars
testinfra_hosts = [sdvars.app_hostname]


JOURNALIST_PUB = "/var/lib/securedrop/journalist.pub"
WEAK_KEY_CONTENTS = (
    Path(__file__).parent.parent.parent.parent / "redwood/res/weak_sample_key.asc"
).read_text()


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


@pytest.mark.skip_in_prod
def test_weak_submission_key(host):
    """
    If the Submission Key is weak (e.g. has a SHA-1 signature),
    the JI should be down (500) and SI will return a 503.
    """
    with host.sudo():
        old_public_key = host.file(JOURNALIST_PUB).content_string
        try:
            # Install a weak key
            set_public_key(host, WEAK_KEY_CONTENTS)
            assert host.run("systemctl restart apache2").rc == 0
            # Now try to hit the JI
            response = host.run("curl -Li http://localhost:8080/").stdout
            assert "HTTP/1.1 500 Internal Server Error" in response
            # Now hit the SI
            response = host.run("curl -i http://localhost:80/").stdout
            assert "HTTP/1.1 503 SERVICE UNAVAILABLE" in response  # Flask shouts
            assert "We're sorry, our SecureDrop is currently offline." in response

        finally:
            set_public_key(host, old_public_key)
            assert host.run("systemctl restart apache2").rc == 0


def set_public_key(host, pubkey: str) -> None:
    """apparently testinfra doesn't provide a function to write a file?"""
    res = host.run(
        f"/usr/bin/python3 -c "
        f'\'import pathlib; pathlib.Path("{JOURNALIST_PUB}")'
        f'.write_text("""{pubkey}""".strip())\''
    )
    print(res.stderr)
    assert res.rc == 0
