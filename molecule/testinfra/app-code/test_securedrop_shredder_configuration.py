import testutils

sdvars = testutils.securedrop_test_vars
testinfra_hosts = [sdvars.app_hostname]


def test_securedrop_shredder_service(host):
    """
    Verify configuration of securedrop_shredder systemd service.
    """
    securedrop_test_vars = sdvars
    service_file = "/lib/systemd/system/securedrop_shredder.service"
    expected_content = "\n".join(
        [
            "[Unit]",
            "Description=SecureDrop shredder",
            "",
            "[Service]",
            'Environment=PYTHONPATH="{}:{}"'.format(
                securedrop_test_vars.securedrop_code,
                securedrop_test_vars.securedrop_venv_site_packages,
            ),
            "ExecStart={}/python /var/www/securedrop/scripts/shredder --interval 60".format(
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

    s = host.service("securedrop_shredder")
    assert s.is_enabled
    assert s.is_running
