import os
from subprocess import check_output
import re
import pytest

SECUREDROP_TARGET_PLATFORM = os.environ.get("SECUREDROP_TARGET_PLATFORM")
testinfra_hosts = [
        "docker://{}-sd-sec-update".format(SECUREDROP_TARGET_PLATFORM)
]


def is_rc_version():
    command = "git symbolic-ref -q --short HEAD || git describe --tags --exact-match"
    version = check_output(command, shell=True).\
        decode("utf8")[0:-1]
    result = re.match(r"(^[\d]+\.[\d]+\.[\d]+-rc[\d]+)|(^update-builder.*)", version)
    if result:
        return True
    else:
        return False


@pytest.mark.skipif(not is_rc_version(), reason="Only tested for RCs")
def test_ensure_no_updates_avail(host):
    """
        Test to make sure that there are no security-updates in the
        base builder container.
    """
    # Filter out all the security repos to their own file
    # without this change all the package updates appeared as if they were
    # coming from normal ubuntu update channel (since they get posted to both)
    host.run('egrep "^deb.*security" /etc/apt/sources.list > /tmp/sec.list')

    dist_upgrade_simulate = host.run('apt-get -s dist-upgrade '
                                     '-oDir::Etc::Sourcelist=/tmp/sec.list '
                                     '|grep "^Inst" |grep -i security')

    # If the grep was successful that means security package updates found
    # otherwise we get a non-zero exit code so no updates needed.
    assert dist_upgrade_simulate.rc != 0
