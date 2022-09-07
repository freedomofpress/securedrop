import functools

FOCAL_VERSION = "20.04"


@functools.lru_cache()
def get_os_release() -> str:
    with open("/etc/os-release") as f:
        os_release = f.readlines()
        for line in os_release:
            if line.startswith("VERSION_ID="):
                version_id = line.split("=")[1].strip().strip('"')
                break
    return version_id
