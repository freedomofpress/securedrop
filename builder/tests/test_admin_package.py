import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

OS_VERSION = os.environ.get("OS_VERSION", "focal")
SECUREDROP_ROOT = Path(
    subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode().strip()
)
BUILD_DIRECTORY = SECUREDROP_ROOT / f"build/{OS_VERSION}"


def test_admin_paths_are_present():
    """
    Ensures the `securedrop-admin` package contains the specified paths
    """
    wanted_files = [
        "/usr/bin/securedrop-admin",
        "/usr/bin/validate-gpg-key.sh",
        "/usr/bin/securedrop-web-open",
        "/usr/share/securedrop-admin/ansible-base/",
        "/usr/share/securedrop-admin/i18n.json",
        "/usr/share/securedrop-admin/venv/",
    ]
    deb_files = list((BUILD_DIRECTORY).glob("securedrop-admin_*_amd64.deb"))
    assert deb_files, "No securedrop-admin .deb file found"
    path = deb_files[0]
    contents = subprocess.check_output(["dpkg-deb", "-c", str(path)]).decode()
    for wanted_file in wanted_files:
        assert re.search(
            rf"^.* .{wanted_file}$",
            contents,
            re.M,
        )


def test_admin_translations_are_absent():
    """
    Ensures the `securedrop-admin` package does not ship translation catalogs,
    which it doesn't use and which may include non-reproducible compiled .mo files
    """
    deb_files = list((BUILD_DIRECTORY).glob("securedrop-admin_*_amd64.deb"))
    assert deb_files, "No securedrop-admin .deb file found"
    path = deb_files[0]
    contents = subprocess.check_output(["dpkg-deb", "-c", str(path)]).decode()
    assert "/usr/share/securedrop-admin/translations" not in contents


def test_admin_qubes_paths_are_present():
    """
    Ensures the `securedrop-admin-qubes` package contains the specified paths
    """
    wanted_files = [
        "/usr/bin/securedrop-set-site-specific",
        "/etc/paxctld.d/torbrowser.conf",
        "/etc/paxctld.d/firefox-esr.conf",
        "/usr/lib/systemd/system/securedrop-torbrowser-pax.path",
        "/usr/lib/systemd/system/securedrop-torbrowser-pax.service",
        "/etc/firefox/policies/policies.json",
        "/usr/share/applications/press.freedom.SecureDropSourceInterface.desktop",
        "/usr/share/applications/press.freedom.SecureDropJournalistInterface.desktop",
        "/usr/share/applications/press.freedom.SecureDropSshApp.desktop",
        "/usr/share/applications/press.freedom.SecureDropSshMon.desktop",
    ]
    deb_files = list((BUILD_DIRECTORY).glob("securedrop-admin-qubes_*_amd64.deb"))
    assert deb_files, "No securedrop-admin-qubes .deb file found"
    path = deb_files[0]
    contents = subprocess.check_output(["dpkg-deb", "-c", str(path)]).decode()
    for wanted_file in wanted_files:
        assert re.search(
            rf"^.* .{wanted_file}$",
            contents,
            re.M,
        )


def test_admin_qubes_paxctld_config_contents():
    """
    Ensures the paxctld configuration grants the PaX flags Tor Browser needs
    to run on grsec kernels
    """
    wanted_lines = [
        "/home/user/.local/share/torbrowser/tbb/x86_64/tor-browser/Browser/firefox.real m nonroot",
        "/home/user/.local/share/torbrowser/tbb/x86_64/tor-browser/Browser/glxtest m nonroot",
        "/usr/lib/firefox-esr/firefox-esr m nonroot",
        "/usr/lib/firefox-esr/firefox-bin m nonroot",
        "/usr/lib/firefox-esr/glxtest m nonroot",
    ]
    deb_files = list((BUILD_DIRECTORY).glob("securedrop-admin-qubes_*_amd64.deb"))
    assert deb_files, "No securedrop-admin-qubes .deb file found"
    path = deb_files[0]
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.check_output(["dpkg-deb", "-x", str(path), tmpdir])
        conf = Path(tmpdir) / "etc/paxctld.d/torbrowser.conf"
        contents = conf.read_text()
        conf = Path(tmpdir) / "etc/paxctld.d/firefox-esr.conf"
        contents += conf.read_text()
    for wanted_line in wanted_lines:
        assert wanted_line in contents


def test_admin_qubes_firefox_depends_on_firefox_esr():
    """
    Ensures the `securedrop-admin-qubes` package depends on `firefox-esr`,
    which is the browser provisioned for firewall setup on sd-admin
    """
    deb_files = list((BUILD_DIRECTORY).glob("securedrop-admin-qubes_*_amd64.deb"))
    assert deb_files, "No securedrop-admin-qubes .deb file found"
    path = deb_files[0]
    contents = subprocess.check_output(["dpkg-deb", "-I", str(path)]).decode()
    m = re.search(r"^ Depends: (.*)$", contents, re.M)
    assert m, "No Depends field found"
    depends = m.group(1).replace(",", " ").split()
    assert "firefox-esr" in depends


def test_admin_qubes_firefox_policies_contents():
    """
    Ensures the Firefox policies shipped with `securedrop-admin-qubes`
    restrict network access to the local network via a dead proxy, so that
    Firefox on sd-admin can only be used for firewall setup and cannot
    reach the clearnet
    """
    deb_files = list((BUILD_DIRECTORY).glob("securedrop-admin-qubes_*_amd64.deb"))
    assert deb_files, "No securedrop-admin-qubes .deb file found"
    path = deb_files[0]
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.check_output(["dpkg-deb", "-x", str(path), tmpdir])
        policies = Path(tmpdir) / "etc/firefox/policies/policies.json"
        policies_contents = json.loads(policies.read_text())
    proxy = policies_contents["policies"]["Proxy"]
    # All non-local traffic is routed to a proxy that refuses connections
    assert proxy["Mode"] == "manual"
    assert proxy["HTTPProxy"] == "127.0.0.1:9"
    assert proxy["SSLProxy"] == "127.0.0.1:9"
    # The proxy settings cannot be changed by the user
    assert proxy["Locked"] is True
    # Private (RFC1918) ranges bypass the proxy and are directly reachable
    passthrough = proxy["Passthrough"]
    for local_range in (
        "localhost",
        "127.0.0.1",
        "192.168.0.0/16",
        "10.0.0.0/8",
        "172.16.0.0/12",
    ):
        assert local_range in passthrough
    assert policies_contents["policies"]["DisableTelemetry"] is True
    assert policies_contents["policies"]["DisableFirefoxStudies"] is True
    assert policies_contents["policies"]["ManualAppUpdateOnly"] is True
    assert policies_contents["policies"]["DontCheckDefaultBrowser"] is True
