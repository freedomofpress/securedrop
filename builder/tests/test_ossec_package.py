import os
import re
import subprocess
from pathlib import Path

OSSEC_VERSION = "3.6.0"

UBUNTU_VERSION = os.environ.get("UBUNTU_VERSION", "focal")
SECUREDROP_ROOT = Path(
    subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode().strip()
)
BUILD_DIRECTORY = SECUREDROP_ROOT / f"build/{UBUNTU_VERSION}"


def test_ossec_binaries_are_present_agent():
    """
    Inspect the package contents to ensure all ossec agent binaries are properly
    included in the package.
    """
    wanted_files = [
        "/var/ossec/bin/agent-auth",
        "/var/ossec/bin/ossec-syscheckd",
        "/var/ossec/bin/ossec-agentd",
        "/var/ossec/bin/manage_agents",
        "/var/ossec/bin/ossec-control",
        "/var/ossec/bin/ossec-logcollector",
        "/var/ossec/bin/util.sh",
        "/var/ossec/bin/ossec-execd",
    ]
    path = BUILD_DIRECTORY / f"ossec-agent_{OSSEC_VERSION}+{UBUNTU_VERSION}_amd64.deb"
    contents = subprocess.check_output(["dpkg-deb", "-c", str(path)]).decode()
    for wanted_file in wanted_files:
        assert re.search(
            rf"^.* .{wanted_file}$",
            contents,
            re.M,
        )


def test_ossec_binaries_are_present_server():
    """
    Inspect the package contents to ensure all ossec server binaries are properly
    included in the package.
    """
    wanted_files = [
        "/var/ossec/bin/ossec-maild",
        "/var/ossec/bin/ossec-remoted",
        "/var/ossec/bin/ossec-syscheckd",
        "/var/ossec/bin/ossec-makelists",
        "/var/ossec/bin/ossec-logtest",
        "/var/ossec/bin/syscheck_update",
        "/var/ossec/bin/ossec-reportd",
        "/var/ossec/bin/ossec-agentlessd",
        "/var/ossec/bin/manage_agents",
        "/var/ossec/bin/rootcheck_control",
        "/var/ossec/bin/ossec-control",
        "/var/ossec/bin/ossec-dbd",
        "/var/ossec/bin/ossec-csyslogd",
        "/var/ossec/bin/ossec-regex",
        "/var/ossec/bin/agent_control",
        "/var/ossec/bin/ossec-monitord",
        "/var/ossec/bin/clear_stats",
        "/var/ossec/bin/ossec-logcollector",
        "/var/ossec/bin/list_agents",
        "/var/ossec/bin/verify-agent-conf",
        "/var/ossec/bin/syscheck_control",
        "/var/ossec/bin/util.sh",
        "/var/ossec/bin/ossec-analysisd",
        "/var/ossec/bin/ossec-execd",
        "/var/ossec/bin/ossec-authd",
    ]
    path = BUILD_DIRECTORY / f"ossec-server_{OSSEC_VERSION}+{UBUNTU_VERSION}_amd64.deb"
    contents = subprocess.check_output(["dpkg-deb", "-c", str(path)]).decode()
    for wanted_file in wanted_files:
        assert re.search(
            rf"^.* .{wanted_file}$",
            contents,
            re.M,
        )
