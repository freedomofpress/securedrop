import pytest


testinfra_hosts = ["app-staging"]
sdvars = pytest.securedrop_test_vars


@pytest.mark.parametrize('pkg', ['apparmor', 'apparmor-utils'])
def test_apparmor_pkg(host, pkg):
    """ Apparmor package dependencies """
    assert host.package(pkg).is_installed


def test_apparmor_enabled(host):
    """ Check that apparmor is enabled """
    with host.sudo():
        assert host.run("aa-status --enabled").rc == 0


apache2_capabilities = [
    'dac_override',
    'kill',
    'net_bind_service',
    'sys_ptrace'
]


@pytest.mark.parametrize('cap', apache2_capabilities)
def test_apparmor_apache_capabilities(host, cap):
    """ check for exact list of expected app-armor capabilities for apache2 """
    c = host.run("perl -nE \'/^\s+capability\s+(\w+),$/ && say $1\' "
                 "/etc/apparmor.d/usr.sbin.apache2")
    assert cap in c.stdout


def test_apparmor_apache_exact_capabilities(host):
    """ ensure no extra capabilities are defined for apache2 """
    c = host.check_output("grep -ic capability "
                          "/etc/apparmor.d/usr.sbin.apache2")
    assert str(len(apache2_capabilities)) == c


tor_capabilities = ['setgid']


@pytest.mark.parametrize('cap', tor_capabilities)
def test_apparmor_tor_capabilities(host, cap):
    """ check for exact list of expected app-armor capabilities for tor """
    c = host.run("perl -nE \'/^\s+capability\s+(\w+),$/ && "
                 "say $1\' /etc/apparmor.d/usr.sbin.tor")
    assert cap in c.stdout


def test_apparmor_tor_exact_capabilities(host):
    """ ensure no extra capabilities are defined for tor """
    c = host.check_output("grep -ic capability "
                          "/etc/apparmor.d/usr.sbin.tor")
    assert str(len(tor_capabilities)) == c


@pytest.mark.parametrize('profile', [
    'ntpd',
    'apache2',
    'tcpdump',
    'tor',
])
def test_apparmor_ensure_not_disabled(host, profile):
    """
    Explicitly check that enforced profiles are NOT in /etc/apparmor.d/disable
    Polling aa-status only checks the last config that was loaded,
    this ensures it wont be disabled on reboot.
    """
    f = host.file("/etc/apparmor.d/disabled/usr.sbin.{}".format(profile))
    with host.sudo():
        assert not f.exists


@pytest.mark.parametrize('complain_pkg', sdvars.apparmor_complain)
def test_app_apparmor_complain(host, complain_pkg):
    """ Ensure app-armor profiles are in complain mode for staging """
    with host.sudo():
        awk = ("awk '/[0-9]+ profiles.*complain."
               "/{flag=1;next}/^[0-9]+.*/{flag=0}flag'")
        c = host.check_output("aa-status | {}".format(awk))
        assert complain_pkg in c


def test_app_apparmor_complain_count(host):
    """ Ensure right number of app-armor profiles are in complain mode """
    with host.sudo():
        c = host.check_output("aa-status --complaining")
        assert c == str(len(sdvars.apparmor_complain))


@pytest.mark.parametrize('aa_enforced', sdvars.apparmor_enforce)
def test_apparmor_enforced(host, aa_enforced):
    awk = ("awk '/[0-9]+ profiles.*enforce./"
           "{flag=1;next}/^[0-9]+.*/{flag=0}flag'")
    with host.sudo():
        c = host.check_output("aa-status | {}".format(awk))
        assert aa_enforced in c


def test_apparmor_total_profiles(host):
    """ Ensure number of total profiles is sum of enforced and
        complaining profiles """
    with host.sudo():
        total_expected = str(len(sdvars.apparmor_enforce)
                             + len(sdvars.apparmor_complain))
        # Xenial about ~20 profiles, so let's expect
        # *at least* the sum.
        assert host.check_output("aa-status --profiled") >= total_expected


def test_aastatus_unconfined(host):
    """ Ensure that there are no processes that are unconfined but have
        a profile """

    # There should be 0 unconfined processes.
    expected_unconfined = 0

    unconfined_chk = str("{} processes are unconfined but have"
                         " a profile defined".format(expected_unconfined))
    with host.sudo():
        aa_status_output = host.check_output("aa-status")
        assert unconfined_chk in aa_status_output


def test_aa_no_denies_in_syslog(host):
    """ Ensure that there are no apparmor denials in syslog """
    with host.sudo():
        f = host.file("/var/log/syslog")
        assert 'apparmor="DENIED"' not in f.content_string
