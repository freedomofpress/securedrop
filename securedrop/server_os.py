import functools
import subprocess
from datetime import date

FOCAL_VERSION = "20.04"


@functools.lru_cache()
def get_xenial_eol_date() -> date:
    return date(2021, 4, 30)


@functools.lru_cache()
def get_os_release() -> str:
    return subprocess.run(
        ["lsb_release", "--release", "--short"],
        check=True,
        stdout=subprocess.PIPE,
        universal_newlines=True
    ).stdout.strip()


def is_os_past_eol() -> bool:
    """
    Assumption: Any OS that is not Focal is an earlier version of the OS.
    """
    if get_os_release() != FOCAL_VERSION and date.today() > get_xenial_eol_date():
        return True
    return False


def is_os_near_eol() -> bool:
    """
    Assumption: Any OS that is not Focal is an earlier version of the OS.
    """
    if get_os_release() != FOCAL_VERSION and date.today() <= get_xenial_eol_date():
        return True
    return False
