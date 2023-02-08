"""
Basic smoke tests that verify the apps are functioning as expected
"""
import pytest
import testutils

sdvars = testutils.securedrop_test_vars
testinfra_hosts = [sdvars.app_hostname]


@pytest.mark.parametrize(
    "name,url,curl_flags",
    (
        # We pass -L to follow the redirect from / to /login
        ("journalist", "http://localhost:8080/", "L"),
        ("source", "http://localhost:80/", ""),
    ),
)
def test_interface_up(host, name, url, curl_flags):
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
    assert "Powered by" in response
