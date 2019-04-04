#!/bin/bash
# shellcheck disable=SC2086
#
#
# Connect to a docker test instance's VNC session

set -e

# Bomb out if container not running
docker inspect securedrop-dev >/dev/null 2>&1 || (echo "ERROR: SD container not running."; exit 1)

# Maybe we are running macOS
if [ "$(uname -s)" == "Darwin" ]; then
    open "vnc://${USER}:freedom@127.0.0.1:5901" &
    exit 0
fi

# Find our securedrop docker ip
SD_DOCKER_IP="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' securedrop-dev)"

# Quit if the VNC port not found
nc -w5 -z "$SD_DOCKER_IP" 5901 || (echo "ERROR: VNC server not found"; exit 1)

if [ ! "$(which remote-viewer)" ]
then
    printf "\nError: We use the remote-viewer utility to reach Docker via VNC,\n"
    printf "and it is not installed. On Debian or Ubuntu, install it with\n"
    printf "'sudo apt install virt-viewer', or if you use another VNC client,\n"
    printf "consider adding it to this script:\n"
    printf "\n%s\n\n" "$(realpath $0)"
    printf "and submitting a pull request.\n\n"
    exit 1
fi

rv_config="${TMPDIR:-/tmp}/func-vnc.ini"
echo -e "[virt-viewer]\ntype=vnc\nhost=${SD_DOCKER_IP}\nport=5901\npassword=freedom" > "${rv_config}"
remote-viewer "${rv_config}" 2>/dev/null &
