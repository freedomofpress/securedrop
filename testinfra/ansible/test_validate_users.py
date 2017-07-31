import pytest
import os


@pytest.mark.skip(reason="Validation not fully implemented yet")
@pytest.mark.parametrize('username', [
    'root',
    'amnesia',
])
def test_validate_users(LocalCommand, username):
    """
    Check that Ansible halts execution of the playbook if the Admin
    username is set to any disallowed value.
    """
    var_override = "--tags validate --extra-vars ssh_users={}".format(username)
    os.environ['ANSIBLE_ARGS'] = var_override
    c = LocalCommand("vagrant provision /staging/")

    assert c.rc != 0
