import io
import os

import pytest
import yaml

# Lots of parent directories to dig out of the Molecule test dir.
# Could also inspect the Molecule env vars and go from there.
REPO_ROOT = os.path.abspath(
    os.path.join(
        __file__,
        os.path.pardir,
        os.path.pardir,
        os.path.pardir,
        os.path.pardir,
    )
)
ANSIBLE_BASE = os.path.join(REPO_ROOT, "install_files", "ansible-base")


def find_ansible_playbooks():
    """
    Test helper to generate list of filepaths for SecureDrop
    Ansible playbooks. All files will be validated to contain the
    max_fail option.
    """
    playbooks = []
    # Not using os.walk since all SecureDrop playbooks are in top-level
    # of the "ansible-base" directory, and *many* YAML files that are
    # not playbooks reside in subdirectories.
    for f in os.listdir(ANSIBLE_BASE):
        # Assume all YAML files in directory are playbooks.
        if f.endswith(".yml"):
            # Ignore files that are deprecated or require test exceptions
            if f not in ["prod-specific.yml", "build-deb-pkgs.yml"]:
                playbooks.append(os.path.join(ANSIBLE_BASE, f))
    # Sanity checking to make sure list of playbooks is not empty.
    assert len(playbooks) > 0
    return playbooks


@pytest.mark.parametrize("playbook", find_ansible_playbooks())
def test_max_fail_percentage(host, playbook):
    """
    All SecureDrop playbooks should set `max_fail_percentage` to "0"
    on each and every play. Doing so ensures that an error on a single
    host constitutes a play failure.

    In conjunction with the `any_errors_fatal` option, tested separately,
    this will achieve a "fail fast" behavior from Ansible.

    There's no ansible.cfg option to set for max_fail_percentage, which would
    allow for a single DRY update that would apply automatically to all
    invocations of `ansible-playbook`. Therefore this test, which will
    search for the line present in all playbooks.

    Technically it's only necessary that plays targeting multiple hosts use
    the parameter, but we'll play it safe and require it everywhere,
    to avoid mistakes down the road.
    """
    with io.open(playbook, "r") as f:
        playbook_yaml = yaml.safe_load(f)
        # Descend into playbook list structure to validate play attributes.
        for play in playbook_yaml:
            assert "max_fail_percentage" in play
            assert play["max_fail_percentage"] == 0


@pytest.mark.parametrize("playbook", find_ansible_playbooks())
def test_any_errors_fatal(host, playbook):
    """
    All SecureDrop playbooks should set `any_errors_fatal` to "yes"
    on each and every play. In conjunction with `max_fail_percentage` set
    to "0", doing so ensures that any errors will cause an immediate failure
    on the playbook.
    """
    with io.open(playbook, "r") as f:
        playbook_yaml = yaml.safe_load(f)
        # Descend into playbook list structure to validate play attributes.
        for play in playbook_yaml:
            assert "any_errors_fatal" in play
            # Ansible coerces booleans, so bare assert is sufficient
            assert play["any_errors_fatal"]


@pytest.mark.parametrize("playbook", find_ansible_playbooks())
def test_locale(host, playbook):
    """
    The securedrop-prod and securedrop-staging playbooks should
    control the locale in the host environment by setting LC_ALL=C.
    """
    with io.open(os.path.join(ANSIBLE_BASE, playbook), "r") as f:
        playbook_yaml = yaml.safe_load(f)
        for play in playbook_yaml:
            assert "environment" in play
            assert play["environment"]["LC_ALL"] == "C"
