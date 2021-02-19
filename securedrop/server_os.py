from datetime import date

FOCAL_VERSION = "20.04"
XENIAL_EOL_DATE = date(2021, 4, 30)

with open("/etc/lsb-release", "r") as f:
    installed_version = f.readlines()[1].split("=")[1].strip("\n")


def is_os_past_eol() -> bool:
    """
    Assumption: Any OS that is not Focal is an earlier version of the OS.
    """
    if installed_version != FOCAL_VERSION and date.today() > XENIAL_EOL_DATE:
        return True
    return False


def is_os_near_eol() -> bool:
    """
    Assumption: Any OS that is not Focal is an earlier version of the OS.
    """
    if installed_version != FOCAL_VERSION and date.today() <= XENIAL_EOL_DATE:
        return True
    return False
