import os


def test_xvfb_is_installed(Package):
    """
    Ensure apt requirements for Xvfb are present.
    """
    assert Package("xvfb").is_installed


def test_firefox_is_installed(Package, Command):
    """
    The app test suite requires a very specific version of Firefox, for
    compatibility with Selenium. Make sure to check the explicit
    version of Firefox, not just that any version of Firefox is installed.

    In Travis, the Firefox installation is handled via the travis.yml
    file, and so it won't show as installed via dpkg.
    """
    if "TRAVIS" not in os.environ:
        p = Package("firefox")
        assert p.is_installed

    c = Command("firefox --version")
    # Reminder: the rstrip is only necessary for local-context actions,
    # e.g. in Travis, but it's a fine practice in all contexts.
    assert c.stdout.rstrip() == "Mozilla Firefox 46.0.1"


def test_xvfb_service_config(File, Sudo):
    """
    Ensure xvfb service configuration file is present.
    Using Sudo context manager because the expected mode is 700.
    Not sure it's really necessary to have this script by 700; 755
    sounds sufficient.
    """
    with Sudo():
        f = File("/etc/init.d/xvfb")
    assert f.is_file
    assert oct(f.mode) == "0700"
    assert f.user == "root"
    assert f.group == "root"
    # Let's hardcode the entire init script and check for exact match.
    # The pytest output will display a diff if anything is missing.
    xvfb_init_content = """
# This is the /etc/init.d/xvfb script. We use it to launch xvfb at boot in the
# development environment so we can easily run the functional tests.

XVFB=/usr/bin/Xvfb
XVFBARGS=":1 -screen 0 1024x768x24 -ac +extension GLX +render -noreset"
PIDFILE=/var/run/xvfb.pid
case "$1" in
  start)
    echo -n "Starting virtual X frame buffer: Xvfb"
    start-stop-daemon --start --quiet --pidfile $PIDFILE --make-pidfile --background --exec $XVFB -- $XVFBARGS
    echo "."
    ;;
  stop)
    echo -n "Stopping virtual X frame buffer: Xvfb"
    start-stop-daemon --stop --quiet --pidfile $PIDFILE
    echo "."
    ;;
  restart)
    $0 stop
    $0 start
    ;;
  *)
        echo "Usage: /etc/init.d/xvfb {start|stop|restart}"
        exit 1
esac

exit 0
""".lstrip().rstrip()  # noqa
    with Sudo():
        assert f.contains('^XVFB=/usr/bin/Xvfb$')
        assert f.contains('^XVFBARGS=":1 -screen 0 1024x768x24 '
                          '-ac +extension GLX +render -noreset"$')
        assert f.content.rstrip() == xvfb_init_content


def test_xvfb_service_enabled(Command, Sudo):
    """
    Ensure xvfb is configured to start on boot via update-rc.d.
    The `-n` option to update-rc.d is dry-run.

    Using Sudo context manager because the service file is mode 700.
    Not sure it's really necessary to have this script by 700; 755
    sounds sufficient.
    """
    with Sudo():
        c = Command('update-rc.d -n xvfb defaults')
    assert c.rc == 0
    wanted_text = 'System start/stop links for /etc/init.d/xvfb already exist.'
    assert wanted_text in c.stdout


def test_xvfb_display_config(File):
    """
    Ensure DISPLAY environment variable is set on boot, for running
    headless tests via Xvfb.
    """
    f = File('/etc/profile.d/xvfb_display.sh')
    assert f.is_file
    assert oct(f.mode) == "0444"
    assert f.user == "root"
    assert f.group == "root"
    assert f.contains("export DISPLAY=:1\n")


def test_xvfb_service_running(Process, Sudo):
    """
    Ensure that xvfb service is running.

    We can't use the Service module because it expects a "status"
    subcommand for the init script, and our custom version doesn't have
    one. So let's make sure the process is running.
    """
    # Sudo isn't necessary to read out of /proc on development, but is
    # required when running under Grsecurity, which app-staging does.
    # So let's escalate privileges to ensure we can determine service state.
    with Sudo():
        p = Process.get(user="root", comm="Xvfb")
        wanted_args = str('/usr/bin/Xvfb :1 -screen 0 1024x768x24 '
                          '-ac +extension GLX +render -noreset')
        assert p.args == wanted_args
        # We only expect a single process, no children.
        workers = Process.filter(ppid=p.pid)
        assert len(workers) == 0
