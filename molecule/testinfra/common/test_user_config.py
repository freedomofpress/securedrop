import re
import textwrap
import pytest


sdvars = pytest.securedrop_test_vars
testinfra_hosts = [sdvars.app_hostname, sdvars.monitor_hostname]


def test_sudoers_config(host):
    """
    Check sudoers config for passwordless sudo via group membership,
    as well as environment-related hardening.
    """
    f = host.file("/etc/sudoers")
    assert f.is_file
    assert f.user == "root"
    assert f.group == "root"
    assert f.mode == 0o440

    # Restrictive file mode requires sudo for reading, so let's
    # read once and store the content in a var.
    with host.sudo():
        sudoers_config = f.content_string

    # Using re.search rather than `f.contains` since the basic grep
    # matching doesn't support PCRE, so `\s` won't work.
    assert re.search(r'^Defaults\s+env_reset$', sudoers_config, re.M)
    assert re.search(r'^Defaults\s+env_reset$', sudoers_config, re.M)
    assert re.search(r'^Defaults\s+mail_badpass$', sudoers_config, re.M)
    assert re.search(r'Defaults\s+secure_path="/usr/local/sbin:'
                     r'/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"',
                     sudoers_config, re.M)
    assert re.search(r'^%sudo\s+ALL=\(ALL\)\s+NOPASSWD:\s+ALL$',
                     sudoers_config, re.M)
    assert re.search(r'Defaults:%sudo\s+!requiretty', sudoers_config, re.M)


def test_sudoers_tmux_env(host):
    """
    Ensure SecureDrop-specific bashrc additions are present.
    This checks for automatic tmux start on interactive shells.
    If we switch to byobu, we can set `byobu-enabled` and check
    the corresponding settings there.
    """

    host_file = host.file('/etc/profile.d/securedrop_additions.sh')
    expected_content = textwrap.dedent(
        """\
        [[ $- != *i* ]] && return

        which tmux >/dev/null 2>&1 || return

        tmux_attach_via_proc() {
            # If the tmux package is upgraded during the lifetime of a
            # session, attaching with the new binary can fail due to different
            # protocol versions. This function attaches using the reference to
            # the old executable found in the /proc tree of an existing
            # session.
            pid=$(pgrep --newest tmux)
            if test -n "$pid"
            then
                /proc/$pid/exe attach
            fi
            return 1
        }

        if test -z "$TMUX"
        then
            (tmux attach || tmux_attach_via_proc || tmux new-session)
        fi"""
    )
    assert host_file.content_string.strip() == expected_content


def test_tmux_installed(host):
    """
    Ensure the `tmux` package is present, since it's required for the user env.
    When running an interactive SSH session over Tor, tmux should be started
    automatically, to prevent problems if the connection is broken
    unexpectedly, as sometimes happens over Tor. The Admin will be able to
    reconnect to the running tmux session and review command output.
    """
    assert host.package("tmux").is_installed


@pytest.mark.skip_in_prod
def test_sudoers_tmux_env_deprecated(host):
    """
    Previous version of the Ansible config set the tmux config
    in per-user ~/.bashrc, which was redundant. The config has
    since moved to /etc/profile.d, to provide a single point of
    update that applies to all users. Let's make sure that the
    old setting isn't still active.
    """

    admin_user = "vagrant"

    f = host.file("/home/{}/.bashrc".format(admin_user))
    assert not f.contains(r"^. \/etc\/bashrc\.securedrop_additions$")
