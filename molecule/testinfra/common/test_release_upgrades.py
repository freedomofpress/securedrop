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


def test_release_manager_upgrade_channel(host):
    """
    Ensures that the `do-release-upgrade` command will not
    suggest upgrades from Xenial to Bionic (which is untested
    and unsupported.)
    """
    expected_channels = {
        "xenial": "never",
        "focal": "never",
    }

    config_path = "/etc/update-manager/release-upgrades"
    assert host.file(config_path).is_file

    raw_output = host.check_output("grep '^Prompt' {}".format(config_path))
    _, channel = raw_output.split("=")

    expected_channel = expected_channels[host.system_info.codename]
    assert channel == expected_channel


def test_do_release_upgrade_is_installed(host):
    """
    Ensure the `do-release-upgrade` command is present on target systems,
    so that instance Admins can upgrade from Trusty to Xenial.
    """
    assert host.exists("do-release-upgrade")
