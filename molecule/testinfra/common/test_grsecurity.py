import difflib
import io
import os
import warnings

import pytest
import testutils
from jinja2 import Template

sdvars = testutils.securedrop_test_vars
testinfra_hosts = [sdvars.app_hostname, sdvars.monitor_hostname]


def test_ssh_motd_disabled(host):
    """
    Ensure the SSH MOTD (Message of the Day) is disabled.
    Grsecurity balks at Ubuntu's default MOTD.
    """
    f = host.file("/etc/pam.d/sshd")
    assert f.is_file
    assert not f.contains(r"pam\.motd")


@pytest.mark.parametrize(
    "package",
    [
        "linux-image-{}-grsec-securedrop",
        "securedrop-grsec",
    ],
)
def test_grsecurity_apt_packages(host, package):
    """
    Ensure the grsecurity-related apt packages are present on the system.
    Includes the FPF-maintained metapackage, as well as paxctl, for managing
    PaX flags on binaries.
    """
    KERNEL_VERSION = sdvars.grsec_version_focal
    if package.startswith("linux-image"):
        package = package.format(KERNEL_VERSION)
    assert host.package(package).is_installed


@pytest.mark.parametrize(
    "package",
    [
        "linux-signed-image-generic-lts-utopic",
        "linux-signed-image-generic",
        "linux-signed-generic-lts-utopic",
        "linux-signed-generic",
        "^linux-image-.*generic$",
        "^linux-headers-.*",
    ],
)
def test_generic_kernels_absent(host, package):
    """
    Ensure the default Ubuntu-provided kernel packages are absent.
    In the past, conflicting version numbers have caused machines
    to reboot into a non-grsec kernel due to poor handling of
    GRUB_DEFAULT logic. Removing the vendor-provided kernel packages
    prevents accidental boots into non-grsec kernels.
    """
    # Can't use the TestInfra Package module to check state=absent,
    # so let's check by shelling out to `dpkg -l`. Dpkg will automatically
    # honor simple regex in package names.
    c = host.run("dpkg -l {}".format(package))
    assert c.rc == 1
    error_text = "dpkg-query: no packages found matching {}".format(package)
    assert error_text in c.stderr.strip()


def test_grsecurity_lock_file(host):
    """
    Ensure system is rerunning a grsecurity kernel by testing for the
    `grsec_lock` file, which is automatically created by grsecurity.
    """
    f = host.file("/proc/sys/kernel/grsecurity/grsec_lock")
    assert f.mode == 0o600
    assert f.user == "root"
    assert f.size == 0


def test_grsecurity_kernel_is_running(host):
    """
    Make sure the currently running kernel is specific grsec kernel.
    """
    KERNEL_VERSION = sdvars.grsec_version_focal
    c = host.run("uname -r")
    assert c.stdout.strip().endswith("-grsec-securedrop")
    assert c.stdout.strip() == "{}-grsec-securedrop".format(KERNEL_VERSION)


@pytest.mark.parametrize(
    "sysctl_opt",
    [
        ("kernel.grsecurity.grsec_lock", 1),
        ("kernel.grsecurity.rwxmap_logging", 0),
        ("vm.heap_stack_gap", 1048576),
    ],
)
def test_grsecurity_sysctl_options(host, sysctl_opt):
    """
    Check that the grsecurity-related sysctl options are set correctly.
    In production the RWX logging is disabled, to reduce log noise.
    """
    with host.sudo():
        assert host.sysctl(sysctl_opt[0]) == sysctl_opt[1]


def test_grsecurity_paxtest(host):
    """
    Check that paxtest reports the expected mitigations. These are
    "Killed" for most of the checks, with the notable exception of the
    memcpy ones. Only newer versions of paxtest will fail the latter,
    regardless of kernel.
    """
    if not host.exists("/usr/bin/paxtest"):
        warnings.warn("Installing paxtest to run kernel tests")
        with host.sudo():
            host.run("apt-get update && apt-get install -y paxtest")
    try:
        with host.sudo():
            # Log to /tmp to avoid cluttering up /root.
            paxtest_cmd = "paxtest blackhat /tmp/paxtest.log"
            # Select only predictably formatted lines; omit
            # the guesses, since the number of bits can vary
            paxtest_cmd += " | grep -P '^(Executable|Return)'"
            paxtest_results = host.check_output(paxtest_cmd)

        paxtest_template_path = "{}/paxtest_results.j2".format(
            os.path.dirname(os.path.abspath(__file__))
        )

        memcpy_result = "Killed"
        # Versions of paxtest newer than 0.9.12 or so will report
        # "Vulnerable" on memcpy tests, see details in
        # https://github.com/freedomofpress/securedrop/issues/1039
        if host.system_info.codename == "focal":
            memcpy_result = "Vulnerable"
        with io.open(paxtest_template_path, "r") as f:
            paxtest_template = Template(f.read().rstrip())
            paxtest_expected = paxtest_template.render(memcpy_result=memcpy_result)

        # The stdout prints here will only be displayed if the test fails
        for paxtest_diff in difflib.context_diff(
            paxtest_expected.split("\n"), paxtest_results.split("\n")
        ):
            print(paxtest_diff)
        assert paxtest_results == paxtest_expected
    finally:
        with host.sudo():
            host.run("apt-get remove -y paxtest")


def test_apt_autoremove(host):
    """
    Ensure old packages have been autoremoved.
    """
    c = host.run("apt-get --dry-run autoremove")
    assert c.rc == 0
    assert "The following packages will be REMOVED" not in c.stdout


def test_paxctl(host):
    """
    As of Focal, paxctl is not used, and shouldn't be installed.
    """
    p = host.package("paxctl")
    assert not p.is_installed


def test_paxctld_focal(host):
    """
    Focal-specific paxctld config checks.
    Ensures paxctld is running and enabled, and relevant
    exemptions are present in the config file.
    """
    assert host.package("paxctld").is_installed
    f = host.file("/etc/paxctld.conf")
    assert f.is_file

    s = host.service("paxctld")
    assert s.is_enabled
    assert s.is_running

    # The securedrop-grsec metapackage will copy the config
    # out of /opt/ to ensure the file is always clobbered on changes.
    assert host.file("/opt/securedrop/paxctld.conf").is_file

    hostname = host.check_output("hostname -s")
    assert ("app" in hostname) or ("mon" in hostname)

    # Under Focal, apache2 pax flags managed by securedrop-grsec metapackage.
    # Both hosts, app & mon, should have the same exemptions. Check precedence
    # between install-local-packages & apt-test repo for securedrop-grsec.
    if "app" in hostname:
        assert f.contains("^/usr/sbin/apache2\tm")


@pytest.mark.parametrize(
    "kernel_opts",
    [
        "WLAN",
        "NFC",
        "WIMAX",
        "WIRELESS",
        "HAMRADIO",
        "IRDA",
        "BT",
    ],
)
def test_wireless_disabled_in_kernel_config(host, kernel_opts):
    """
    Kernel modules for wireless are blacklisted, but we go one step further and
    remove wireless support from the kernel. Let's make sure wireless is
    disabled in the running kernel config!
    """
    KERNEL_VERSION = sdvars.grsec_version_focal
    with host.sudo():
        kernel_config_path = "/boot/config-{}-grsec-securedrop".format(KERNEL_VERSION)
        kernel_config = host.file(kernel_config_path).content_string

        line = "# CONFIG_{} is not set".format(kernel_opts)
        assert line in kernel_config or kernel_opts not in kernel_config


@pytest.mark.parametrize(
    "kernel_opts",
    [
        "CONFIG_X86_INTEL_TSX_MODE_OFF",
        "CONFIG_PAX",
        "CONFIG_GRKERNSEC",
    ],
)
def test_kernel_options_enabled_config(host, kernel_opts):
    """
    Tests kernel config for options that should be enabled
    """

    KERNEL_VERSION = sdvars.grsec_version_focal
    with host.sudo():
        kernel_config_path = "/boot/config-{}-grsec-securedrop".format(KERNEL_VERSION)
        kernel_config = host.file(kernel_config_path).content_string

        line = "{}=y".format(kernel_opts)
        assert line in kernel_config


def test_mds_mitigations_and_smt_disabled(host):
    """
    Ensure that full mitigations are in place for MDS
    see https://www.kernel.org/doc/html/latest/admin-guide/hw-vuln/mds.html
    """

    with host.sudo():
        grub_config_path = "/boot/grub/grub.cfg"
        grub_config = host.file(grub_config_path)

        assert grub_config.contains("mds=full,nosmt")


def test_kernel_boot_options(host):
    """
    Ensure command-line options for currently booted kernel are set.
    """
    with host.sudo():
        f = host.file("/proc/cmdline")
        boot_opts = f.content_string.split()
    assert "noefi" in boot_opts
    if host.system_info.codename == "focal":
        assert "ipv6.disable=1" in boot_opts
