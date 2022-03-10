import functools
import re
import subprocess

FOCAL_VERSION = "20.04"


@functools.lru_cache()
def get_os_release() -> str:
    return subprocess.run(
        ["/usr/bin/lsb_release", "--release", "--short"],
        check=True,
        stdout=subprocess.PIPE,
        universal_newlines=True
    ).stdout.strip()


@functools.lru_cache()
def get_tor_version() -> str:
    try:
        output = subprocess.run(
            ["/usr/bin/tor", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            universal_newlines=True
        ).stdout.strip()
        # Output looks like: "Tor version 0.4.5.11."
        # There might also be a warning about zstd being the wrong version, the
        # regex should ignore that.
        search = re.search(r"Tor version (.*)\.$", output)
        if search:
            return search.group(1)
    except:  # noqa E722
        # Avoid breaking the entire /metadata endpoint if we can't figure out
        # the Tor version
        pass
    return "unknown"
