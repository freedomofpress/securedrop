def test_haveged_config(File):
    """
    Ensure haveged's low entrop watermark is sufficiently high.
    """
    f = File('/etc/default/haveged')
    assert f.is_file
    assert f.user == 'root'
    assert f.group == 'root'
    assert oct(f.mode) == '0644'
    assert f.contains('^DAEMON_ARGS="-w 2400"$')


def test_haveged_no_duplicate_lines(Command):
    """
    Regression test to check for duplicate entries. Earlier playbooks
    for configuring the SD instances needlessly appended the `DAEMON_ARGS`
    line everytime the playbook was run. Fortunately the duplicate lines don't
    break the service, but it's still poor form.
    """
    c = Command("uniq --repeated /etc/default/haveged")
    assert c.rc == 0
    assert c.stdout == ""


def test_haveged_is_running(Service):
    """
    Ensure haveged service is running, to provide additional entropy.
    """
    s = Service("haveged")
    assert s.is_running
    assert s.is_enabled
