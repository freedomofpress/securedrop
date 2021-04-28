import testutils

test_vars = testutils.securedrop_test_vars
testinfra_hosts = [test_vars.app_hostname, test_vars.monitor_hostname]


def test_release_manager_installed(host):
    """
    The securedrop-config package munges `do-release-upgrade` settings
    that assume the release-upgrader logic is installed. On hardware
    installs of Ubuntu, it is, but the VM images we use in CI may
    remove it to make the boxes leaner.
    """
    assert host.package("ubuntu-release-upgrader-core").is_installed
    assert host.exists("do-release-upgrade")


def test_release_manager_upgrade_channel(host):
    """
    Ensures that the `do-release-upgrade` command will not
    suggest upgrades to a future LTS, until we test it and provide support.
    """
    config_path = "/etc/update-manager/release-upgrades"
    assert host.file(config_path).is_file

    raw_output = host.check_output("grep '^Prompt' {}".format(config_path))
    _, channel = raw_output.split("=")

    assert channel == "never"
