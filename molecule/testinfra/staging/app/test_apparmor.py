import pytest


sdvars = pytest.securedrop_test_vars


@pytest.mark.parametrize('pkg', ['apparmor', 'apparmor-utils'])
def test_apparmor_pkg(Package, pkg):
    """ Apparmor package dependencies """
    assert Package(pkg).is_installed


def test_apparmor_enabled(Command, Sudo):
    """ Check that apparmor is enabled """
    with Sudo():
        assert Command("aa-status --enabled").rc == 0


apache2_capabilities = [
        'dac_override',
        'kill',
        'net_bind_service',
        'sys_ptrace'
        ]


@pytest.mark.parametrize('cap', apache2_capabilities)
def test_apparmor_apache_capabilities(Command, cap):
    """ check for exact list of expected app-armor capabilities for apache2 """
    c = Command("perl -nE \'/^\s+capability\s+(\w+),$/ && say $1\' "
                "/etc/apparmor.d/usr.sbin.apache2")
    assert cap in c.stdout


def test_apparmor_apache_exact_capabilities(Command):
    """ ensure no extra capabilities are defined for apache2 """
    c = Command.check_output("grep -ic capability "
                             "/etc/apparmor.d/usr.sbin.apache2")
    assert str(len(apache2_capabilities)) == c


tor_capabilities = ['setgid']


@pytest.mark.parametrize('cap', tor_capabilities)
def test_apparmor_tor_capabilities(Command, cap):
    """ check for exact list of expected app-armor capabilities for tor """
    c = Command("perl -nE \'/^\s+capability\s+(\w+),$/ && "
                "say $1\' /etc/apparmor.d/usr.sbin.tor")
    assert cap in c.stdout


def test_apparmor_tor_exact_capabilities(Command):
    """ ensure no extra capabilities are defined for tor """
    c = Command.check_output("grep -ic capability "
                             "/etc/apparmor.d/usr.sbin.tor")
    assert str(len(tor_capabilities)) == c


enforced_profiles = [
        'ntpd',
        'apache2',
        'tcpdump',
        'tor']


@pytest.mark.parametrize('profile', enforced_profiles)
def test_apparmor_ensure_not_disabled(File, Sudo, profile):
    """ Explicitly check that enforced profiles are NOT in
        /etc/apparmor.d/disable
        Polling aa-status only checks the last config that was loaded,
        this ensures it wont be disabled on reboot.
    """
    f = File("/etc/apparmor.d/disabled/usr.sbin.{}".format(profile))
    with Sudo():
        assert not f.exists


@pytest.mark.parametrize('complain_pkg', sdvars.apparmor_complain)
def test_app_apparmor_complain(Command, Sudo, complain_pkg):
    """ Ensure app-armor profiles are in complain mode for staging """
    with Sudo():
        awk = ("awk '/[0-9]+ profiles.*complain."
               "/{flag=1;next}/^[0-9]+.*/{flag=0}flag'")
        c = Command.check_output("aa-status | {}".format(awk))
        assert complain_pkg in c


def test_app_apparmor_complain_count(Command, Sudo):
    """ Ensure right number of app-armor profiles are in complain mode """
    with Sudo():
        c = Command.check_output("aa-status --complaining")
        assert c == str(len(sdvars.apparmor_complain))


@pytest.mark.parametrize('aa_enforced', sdvars.apparmor_enforce)
def test_apparmor_enforced(Command, Sudo, aa_enforced):
    awk = ("awk '/[0-9]+ profiles.*enforce./"
           "{flag=1;next}/^[0-9]+.*/{flag=0}flag'")
    with Sudo():
        c = Command.check_output("aa-status | {}".format(awk))
        assert aa_enforced in c


def test_apparmor_total_profiles(Command, Sudo):
    """ Ensure number of total profiles is sum of enforced and
        complaining profiles """
    with Sudo():
        total_expected = str((len(sdvars.apparmor_enforce)
                             + len(sdvars.apparmor_complain)))
        assert Command.check_output("aa-status --profiled") == total_expected


def test_aastatus_unconfined(Command, Sudo):
    """ Ensure that there are no processes that are unconfined but have
        a profile """
    unconfined_chk = "0 processes are unconfined but have a profile defined"
    with Sudo():
        assert unconfined_chk in Command("aa-status").stdout
