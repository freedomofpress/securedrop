import atexit
import os
import select
import signal
import subprocess
import sys

__all__ = ['run']


def colorize(s, color, bold=False):
    """
    Returns the string s surrounded by shell metacharacters to display
    it with the given color and optionally bolded.
    """
    # List of shell colors from https://www.siafoo.net/snippet/88
    shell_colors = {
        'gray': '30',
        'red': '31',
        'green': '32',
        'yellow': '33',
        'blue': '34',
        'magenta': '35',
        'cyan': '36',
        'white': '37',
        'crimson': '38',
        'highlighted_red': '41',
        'highlighted_green': '42',
        'highlighted_brown': '43',
        'highlighted_blue': '44',
        'highlighted_magenta': '45',
        'highlighted_cyan': '46',
        'highlighted_gray': '47',
        'highlighted_crimson': '48'
    }

    # Based on http://stackoverflow.com/a/2330297/1093000
    attrs = []
    attrs.append(shell_colors[color])
    if bold:
        attrs.append('1')

    return '\x1b[{}m{}\x1b[0m'.format(';'.join(attrs), s)


class DevServerProcess(subprocess.Popen):

    def __init__(self, label, cmd, color):
        self.label = label
        self.cmd = cmd
        self.color = color

        super(DevServerProcess, self).__init__(
            self.cmd,
            stdin  = subprocess.PIPE,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,
            preexec_fn = os.setsid)

    def print_label(self, to):
        label = "\n => {} <= \n\n".format(self.label)
        if to.isatty():
            label = colorize(label, self.color, True)
        to.write(label)

    def fileno(self):
        """
        Implement fileno() in order to use DevServerProcesses with select.select
        directly.

        Note this method assumes we only want to select this process'
        stdout. This is a reafsonable assumption for a DevServerProcess
        because the __init__ redirects stderr to stdout, so all output is
        available on stdout.
        """
        return self.stdout.fileno()


class DevServerProcessMonitor(object):

    def __init__(self, procs):
        self.procs = procs
        self.last_proc = None
        atexit.register(self.cleanup)

    def monitor(self):
        while True:
            # TODO: we currently don't handle input, which makes using an
            # interactive debugger like pdb impossible. Since Flask provides
            # a featureful in-browser debugger, I'll accept that pdb is
            # broken for now. If someone really wants it, they should be
            # able to change this function to make it work (although I'm not
            # sure how hard that would be).
            #
            # If you really want to use pdb, you can just run the
            # application scripts individually (`python source.py` or
            # `python journalist.py`).
            rprocs, _, _ = select.select(self.procs, [], [])

            for proc in rprocs:
                # To keep track of which process output what, print a
                # helpful label every time the process sending output
                # changes.
                if proc != self.last_proc:
                    proc.print_label(sys.stdout)
                    self.last_proc = proc

                line = proc.stdout.readline()
                sys.stdout.write(line)
                sys.stdout.flush()

            if any(proc.poll() is not None for proc in self.procs):
                # If any of the processes terminates (for example, due to
                # a syntax error causing a reload to fail), kill them all
                # so we don't get stuck.
                sys.stdout.write(colorize(
                    "\nOne of the development servers exited unexpectedly. "
                    "See the traceback above for details.\n"
                    "Once you have resolved the issue, you can re-run "
                    "'./manage.py run' to continue developing.\n\n",
                    "red", True))
                self.cleanup()
                break

        for proc in self.procs:
            proc.wait()

    def cleanup(self):
        for proc in self.procs:
            if proc.poll() is None:
                # When the development servers use automatic reloading, they
                # spawn new subprocesses frequently. In order to make sure we
                # kill all of the subprocesses, we need to send SIGTERM to
                # the process group and not just the process we initially
                # created. See http://stackoverflow.com/a/4791612/1093000
                os.killpg(proc.pid, signal.SIGTERM)
                proc.terminate()


def run():
    """
    Starts development servers for both the Source Interface and the
    Document Interface concurrently. Their output is collected,
    labeled, and sent to stdout to present a unified view to the
    developer.

    Ctrl-C will kill the servers and return you to the terminal.

    Useful resources:
    * https://stackoverflow.com/questions/22565606/python-asynhronously-print-stdout-from-multiple-subprocesses

    """
    procs = [
        DevServerProcess('Source Interface',
                         ['python', 'source.py'],
                         'blue'),
        DevServerProcess('Document Interface',
                         ['python', 'journalist.py'],
                         'cyan'),
    ]

    monitor = DevServerProcessMonitor(procs)
    monitor.monitor()
