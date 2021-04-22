import functools
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
