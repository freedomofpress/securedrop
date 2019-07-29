import pytest
import re


testinfra_hosts = ["app-staging"]
securedrop_test_vars = pytest.securedrop_test_vars


@pytest.mark.parametrize(
    "config_line",
    [
        "[program:securedrop_rqrequeue]",
        (
            "command=/opt/venvs/securedrop-app-code/bin/python "
            "/var/www/securedrop/scripts/rqrequeue --interval 60"
        ),
        "directory={}".format(securedrop_test_vars.securedrop_code),
        (
            'environment=PYTHONPATH="/var/www/securedrop:'
            '/opt/venvs/securedrop-app-code/lib/python3.5/site-packages"'
        ),
        "autostart=true",
        "autorestart=true",
        "startretries=3",
        "stderr_logfile=/var/log/securedrop_worker/rqrequeue.err",
        "stdout_logfile=/var/log/securedrop_worker/rqrequeue.out",
        "user={}".format(securedrop_test_vars.securedrop_user),
    ],
)
def test_rqrequeue_configuration(host, config_line):
    """
    Ensure Supervisor config for rqrequeue is correct.
    """
    f = host.file("/etc/supervisor/conf.d/securedrop_rqrequeue.conf")
    # Config lines may have special characters such as [] which will
    # throw off the regex matching, so let's escape those chars.
    regex = re.escape(config_line)
    assert f.contains("^{}$".format(regex))


def test_rqrequeue_config_file(host):
    """
    Check ownership and mode of Supervisor config for rqrequeue.

    Using separate test so that the parametrization doesn't rerun
    the file mode checks, which would be useless.
    """
    f = host.file("/etc/supervisor/conf.d/securedrop_rqrequeue.conf")
    assert f.is_file
    assert f.mode == 0o644
    assert f.user == "root"
    assert f.group == "root"
