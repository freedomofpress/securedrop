import testutils

securedrop_test_vars = testutils.securedrop_test_vars
testinfra_hosts = [securedrop_test_vars.app_hostname]


def test_securedrop_rqrequeue_service(host):
    """
    Verify configuration of securedrop_rqrequeue systemd service.
    """
    service_file = "/lib/systemd/system/securedrop_rqrequeue.service"
    expected_content = "\n".join(
        [
            "[Unit]",
            "Description=SecureDrop rqrequeue process",
            "After=redis-server.service",
            "Wants=redis-server.service",
            "",
            "[Service]",
            'Environment=PYTHONPATH="{}:{}"'.format(
                securedrop_test_vars.securedrop_code,
                securedrop_test_vars.securedrop_venv_site_packages,
            ),
            "ExecStart={}/python /var/www/securedrop/scripts/rqrequeue --interval 60".format(
                securedrop_test_vars.securedrop_venv_bin
            ),
            "PrivateDevices=yes",
            "PrivateTmp=yes",
            "ProtectSystem=full",
            "ReadOnlyDirectories=/",
            "ReadWriteDirectories={}".format(securedrop_test_vars.securedrop_data),
            "Restart=always",
            "RestartSec=10s",
            "UMask=077",
            "User={}".format(securedrop_test_vars.securedrop_user),
            "WorkingDirectory={}".format(securedrop_test_vars.securedrop_code),
            "",
            "[Install]",
            "WantedBy=multi-user.target\n",
        ]
    )

    f = host.file(service_file)
    assert f.is_file
    assert f.mode == 0o644
    assert f.user == "root"
    assert f.group == "root"
    assert f.content_string == expected_content

    s = host.service("securedrop_rqrequeue")
    assert s.is_enabled
    assert s.is_running
