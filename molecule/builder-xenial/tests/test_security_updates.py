import os
SECUREDROP_TARGET_PLATFORM = os.environ.get("SECUREDROP_TARGET_PLATFORM")
testinfra_hosts = [
        "docker://{}-sd-sec-update".format(SECUREDROP_TARGET_PLATFORM)
]


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
