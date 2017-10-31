import pytest
import os
import re


def test_ssh_motd_disabled(File):
    """
    Ensure the SSH MOTD (Message of the Day) is disabled.
    Grsecurity balks at Ubuntu's default MOTD.
    """
    f = File("/etc/pam.d/sshd")
    assert f.is_file
    assert not f.contains("pam\.motd")


@pytest.mark.skipif(os.environ.get('FPF_GRSEC', 'true') == "false",
                    reason="Need to skip in environment w/o grsec")
@pytest.mark.parametrize("package", [
    'paxctl',
    'securedrop-grsec',
])
def test_grsecurity_apt_packages(Package, package):
    """
    Ensure the grsecurity-related apt packages are present on the system.
    Includes the FPF-maintained metapackage, as well as paxctl, for managing
    PaX flags on binaries.
    """
    assert Package(package).is_installed


@pytest.mark.skipif(os.environ.get('FPF_GRSEC', 'true') == "false",
                    reason="Need to skip in environment w/o grsec")
@pytest.mark.parametrize("package", [
    'linux-signed-image-generic-lts-utopic',
    'linux-signed-image-generic',
    'linux-signed-generic-lts-utopic',
    'linux-signed-generic',
    '^linux-image-.*generic$',
    '^linux-headers-.*',
])
def test_generic_kernels_absent(Command, package):
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
    c = Command("dpkg -l {}".format(package))
    assert c.rc == 1
    error_text = "dpkg-query: no packages found matching {}".format(package)
    assert c.stderr == error_text


@pytest.mark.skipif(os.environ.get('FPF_GRSEC', 'true') == "false",
                    reason="Need to skip in environment w/o grsec")
def test_grsecurity_lock_file(File):
    """
    Ensure system is rerunning a grsecurity kernel by testing for the
    `grsec_lock` file, which is automatically created by grsecurity.
    """
    f = File("/proc/sys/kernel/grsecurity/grsec_lock")
    assert oct(f.mode) == "0600"
    assert f.user == "root"
    assert f.size == 0


@pytest.mark.skipif(os.environ.get('FPF_GRSEC', 'true') == "false",
                    reason="Need to skip in environment w/o grsec")
def test_grsecurity_kernel_is_running(Command):
    """
    Make sure the currently running kernel is specific grsec kernel.
    """
    c = Command('uname -r')
    assert c.stdout.endswith('-grsec')
    assert c.stdout == '3.14.79-grsec'


@pytest.mark.skipif(os.environ.get('FPF_GRSEC', 'true') == "false",
                    reason="Need to skip in environment w/o grsec")
@pytest.mark.parametrize('sysctl_opt', [
  ('kernel.grsecurity.grsec_lock', 1),
  ('kernel.grsecurity.rwxmap_logging', 0),
  ('vm.heap_stack_gap', 1048576),
])
def test_grsecurity_sysctl_options(Sysctl, Sudo, sysctl_opt):
    """
    Check that the grsecurity-related sysctl options are set correctly.
    In production the RWX logging is disabled, to reduce log noise.
    """
    with Sudo():
        assert Sysctl(sysctl_opt[0]) == sysctl_opt[1]


@pytest.mark.skipif(os.environ.get('FPF_GRSEC', 'true') == "false",
                    reason="Need to skip in environment w/o grsec")
@pytest.mark.parametrize('paxtest_check', [
  "Executable anonymous mapping",
  "Executable bss",
  "Executable data",
  "Executable heap",
  "Executable stack",
  "Executable shared library bss",
  "Executable shared library data",
  "Executable anonymous mapping (mprotect)",
  "Executable bss (mprotect)",
  "Executable data (mprotect)",
  "Executable heap (mprotect)",
  "Executable stack (mprotect)",
  "Executable shared library bss (mprotect)",
  "Executable shared library data (mprotect)",
  "Writable text segments",
  "Return to function (memcpy)",
  "Return to function (memcpy, PIE)",
])
def test_grsecurity_paxtest(Command, Sudo, paxtest_check):
    """
    Check that paxtest does not report anything vulnerable
    Requires the package paxtest to be installed.
    The paxtest package is currently being installed in the app-test role.
    """
    if Command.exists("/usr/bin/paxtest"):
        with Sudo():
            c = Command("paxtest blackhat")
            assert c.rc == 0
            assert "Vulnerable" not in c.stdout
            regex = "^{}\s*:\sKilled$".format(re.escape(paxtest_check))
            assert re.search(regex, c.stdout)


@pytest.mark.skipif(os.environ.get('FPF_CI', 'false') == "true",
                    reason="Not needed in CI environment")
def test_grub_pc_marked_manual(Command):
    """
    Ensure the `grub-pc` packaged is marked as manually installed.
    This is necessary for VirtualBox with Vagrant.
    """
    c = Command('apt-mark showmanual grub-pc')
    assert c.rc == 0
    assert c.stdout == "grub-pc"


@pytest.mark.skipif(os.environ.get('FPF_GRSEC', 'true') == "false",
                    reason="Need to skip in environment w/o grsec")
def test_apt_autoremove(Command):
    """
    Ensure old packages have been autoremoved.
    """
    c = Command('apt-get --dry-run autoremove')
    assert c.rc == 0
    assert "The following packages will be REMOVED" not in c.stdout


@pytest.mark.skipif(os.environ.get('FPF_GRSEC', 'true') == "false",
                    reason="Need to skip in environment w/o grsec")
@pytest.mark.parametrize("binary", [
    "/usr/sbin/grub-probe",
    "/usr/sbin/grub-mkdevicemap",
    "/usr/bin/grub-script-check",
])
def test_pax_flags(Command, File, binary):
    """
    Ensure PaX flags are set correctly on critical Grub binaries.
    These flags are maintained as part of a post-install kernel hook
    in the `securedrop-grsec` metapackage. If they aren't set correctly,
    the machine may fail to boot into a new kernel.
    """

    f = File("/etc/kernel/postinst.d/paxctl-grub")
    assert f.is_file
    assert f.contains("^paxctl -zCE {}".format(binary))

    c = Command("paxctl -v {}".format(binary))
    assert c.rc == 0

    assert "- PaX flags: --------E--- [{}]".format(binary) in c.stdout
    assert "EMUTRAMP is enabled" in c.stdout
    # Tracking regressions; previous versions of the Ansible config set
    # the "p" and "m" flags.
    assert "PAGEEXEC is disabled" not in c.stdout
    assert "MPROTECT is disabled" not in c.stdout
