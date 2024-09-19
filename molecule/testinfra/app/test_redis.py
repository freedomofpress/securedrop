"""
Test redis is configured as desired
"""

import re

import testutils

sdvars = testutils.securedrop_test_vars
testinfra_hosts = [sdvars.app_hostname]


def test_auth_required(host):
    """
    Verify the redis server requires authentication
    """
    response = host.run("bash -c 'echo \"PING\" | redis-cli'").stdout.strip()
    assert response == "NOAUTH Authentication required."


def test_password_works(host):
    """
    Verify the redis password works
    """
    f = host.file("/var/www/securedrop/rq_config.py")
    with host.sudo():
        # First let's check file permissions
        assert f.is_file
        assert f.user == "root"
        assert f.group == "www-data"
        assert f.mode == 0o640
        contents = f.content_string
    password = re.search('"(.*?)"', contents).group(1)
    # Now run an authenticated PING
    response = host.run(
        f'bash -c \'echo "PING" | REDISCLI_AUTH="{password}" redis-cli\''
    ).stdout.strip()
    assert response == "PONG"
