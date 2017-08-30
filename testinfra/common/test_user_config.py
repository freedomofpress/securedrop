import os
import pytest
import re

hostenv = os.environ['SECUREDROP_TESTINFRA_TARGET_HOST']


def test_sudoers_config(File, Sudo):
    """
    Check sudoers config for passwordless sudo via group membership,
    as well as environment-related hardening.
    """
    f = File("/etc/sudoers")
    assert f.is_file
    assert f.user == "root"
    assert f.group == "root"
    assert oct(f.mode) == "0440"

    # Restrictive file mode requires sudo for reading, so let's
    # read once and store the content in a var.
    with Sudo():
        sudoers_config = f.content

    # Using re.search rather than `f.contains` since the basic grep
    # matching doesn't support PCRE, so `\s` won't work.
    assert re.search('^Defaults\s+env_reset$', sudoers_config, re.M)
    assert re.search('^Defaults\s+env_reset$', sudoers_config, re.M)
    assert re.search('^Defaults\s+mail_badpass$', sudoers_config, re.M)
    assert re.search('Defaults\s+secure_path="/usr/local/sbin:'
                     '/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"',
                     sudoers_config, re.M)
    assert re.search('^%sudo\s+ALL=\(ALL\)\s+NOPASSWD:\s+ALL$',
                     sudoers_config, re.M)
    assert re.search('Defaults:%sudo\s+!requiretty', sudoers_config, re.M)


def test_sudoers_tmux_env(File):
    """
    Ensure SecureDrop-specific bashrc additions are present.
    This checks for automatic tmux start on interactive shells.
    If we switch to byobu, we can set `byobu-enabled` and check
    the corresponding settings there.
    """

    f = File('/etc/profile.d/securedrop_additions.sh')
    non_interactive_str = re.escape('[[ $- != *i* ]] && return')
    tmux_check = re.escape('test -z "$TMUX" && (tmux attach ||'
                           ' tmux new-session)')

    assert f.contains("^{}$".format(non_interactive_str))
    assert f.contains("^if which tmux >\/dev\/null 2>&1; then$")

    assert 'test -z "$TMUX" && (tmux attach || tmux new-session)' in f.content
    assert f.contains(tmux_check)


def test_tmux_installed(Package):
    """
    Ensure the `tmux` package is present, since it's required for the user env.
    When running an interactive SSH session over Tor, tmux should be started
    automatically, to prevent problems if the connection is broken
    unexpectedly, as sometimes happens over Tor. The Admin will be able to
    reconnect to the running tmux session and review command output.
    """
    assert Package("tmux").is_installed


@pytest.mark.skipif(hostenv == 'travis',
                    reason="Bashrc tests dont make sense on Travis")
def test_sudoers_tmux_env_deprecated(File):
    """
    Previous version of the Ansible config set the tmux config
    in per-user ~/.bashrc, which was redundant. The config has
    since moved to /etc/profile.d, to provide a single point of
    update that applies to all users. Let's make sure that the
    old setting isn't still active.
    """

    admin_user = "vagrant"
    if os.environ.get("FPF_CI", None):
        admin_user = "sdrop"

    f = File("/home/{}/.bashrc".format(admin_user))
    assert not f.contains("^. \/etc\/bashrc\.securedrop_additions$")
