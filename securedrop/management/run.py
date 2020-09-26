import atexit
import os
import select
import signal
import subprocess
import sys

__all__ = ['run']

from typing import Any

from typing import List
from typing import TextIO

from typing import Callable


def colorize(s: str, color: str, bold: bool = False) -> str:
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


class DevServerProcess(subprocess.Popen):  # pragma: no cover

    def __init__(self, label: str, cmd: List[str], color: str) -> None:
        self.label = label
        self.cmd = cmd
        self.color = color

        super(DevServerProcess, self).__init__(  # type: ignore
            self.cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid)

    def print_label(self, to: TextIO) -> None:
        label = "\n => {} <= \n\n".format(self.label)
        if to.isatty():
            label = colorize(label, self.color, True)
        to.write(label)

    def fileno(self) -> int:
        """Implement fileno() in order to use DevServerProcesses with
        select.select directly.

        Note this method assumes we only want to select this process'
        stdout. This is a reasonable assumption for a DevServerProcess
        because the __init__ redirects stderr to stdout, so all output is
        available on stdout.

        """
        if not self.stdout:
            raise RuntimeError()
        return self.stdout.fileno()


class DevServerProcessMonitor:  # pragma: no cover

    def __init__(self, proc_funcs: List[Callable]) -> None:
        self.procs = []
        self.last_proc = None
        atexit.register(self.cleanup)

        for pf in proc_funcs:
            self.procs.append(pf())

    def monitor(self) -> None:
        while True:
            rprocs, _, _ = select.select(self.procs, [], [])

            for proc in rprocs:
                # To keep track of which process output what, print a
                # helpful label every time the process sending output
                # changes.
                if proc != self.last_proc:
                    proc.print_label(sys.stdout)
                    self.last_proc = proc

                line = proc.stdout.readline()
                sys.stdout.write(line.decode('utf-8'))
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

    def cleanup(self) -> None:
        for proc in self.procs:
            if proc.poll() is None:
                # When the development servers use automatic reloading, they
                # spawn new subprocesses frequently. In order to make sure we
                # kill all of the subprocesses, we need to send SIGTERM to
                # the process group and not just the process we initially
                # created. See http://stackoverflow.com/a/4791612/1093000
                os.killpg(proc.pid, signal.SIGTERM)
                proc.terminate()


def run(args: Any) -> None:  # pragma: no cover
    """
    Starts development servers for both the Source Interface and the
    Journalist Interface concurrently. Their output is collected,
    labeled, and sent to stdout to present a unified view to the
    developer.

    Ctrl-C will kill the servers and return you to the terminal.

    Useful resources:
    * https://stackoverflow.com/q/22565606/837471

    """
    print("""
 ____                                        ____                           
/\\  _`\\                                     /\\  _`\\                         
\\ \\,\\L\\_\\     __    ___   __  __  _ __    __\\ \\ \\/\\ \\  _ __   ___   _____   
 \\/_\\__ \\   /'__`\\ /'___\\/\\ \\/\\ \\/\\`'__\\/'__`\\ \\ \\ \\ \\/\\`'__\\/ __`\\/\\ '__`\\ 
   /\\ \\L\\ \\/\\  __//\\ \\__/\\ \\ \\_\\ \\ \\ \\//\\  __/\\ \\ \\_\\ \\ \\ \\//\\ \\L\\ \\ \\ \\L\\ \\
   \\ `\\____\\ \\____\\ \\____\\\\ \\____/\\ \\_\\\\ \\____\\\\ \\____/\\ \\_\\\\ \\____/\\ \\ ,__/
    \\/_____/\\/____/\\/____/ \\/___/  \\/_/ \\/____/ \\/___/  \\/_/ \\/___/  \\ \\ \\/ 
                                                                      \\ \\_\\ 
                                                                       \\/_/ 
""")  # noqa

    procs = [
        lambda: DevServerProcess('Source Interface',
                                 ['python', 'source.py'],
                                 'blue'),
        lambda: DevServerProcess('Journalist Interface',
                                 ['python', 'journalist.py'],
                                 'cyan'),
        lambda: DevServerProcess('SASS Compiler',
                                 ['sass', '--watch', 'sass:static/css'],
                                 'magenta'),
    ]

    monitor = DevServerProcessMonitor(procs)
    monitor.monitor()
