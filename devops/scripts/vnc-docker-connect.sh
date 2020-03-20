#!/bin/bash
# shellcheck disable=SC2086,SC2230
#
#
# Connect to a docker test instance's VNC session

set -e

PORT_OFFSET=${PORT_OFFSET:-100}

# Bomb out if container not running
docker inspect securedrop-dev-${PORT_OFFSET} >/dev/null 2>&1 || (echo "ERROR: SD container not running."; exit 1)

VNCPORT=$((PORT_OFFSET + 5909))

echo "Connecting to container securedrop-dev-${PORT_OFFSET}:${VNCPORT}..."

# Maybe we are running macOS
if [ "$(uname -s)" == "Darwin" ]; then
    open "vnc://${USER}:freedom@127.0.0.1:${VNCPORT}" &
    exit 0
fi

# Quit if the VNC port not found
nc -w5 -z "127.0.0.1" ${VNCPORT} || (echo "ERROR: VNC server not found"; exit 1)

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


rv_config="${TMPDIR:-/tmp}/sd-vnc.ini"
echo -e "[virt-viewer]\ntype=vnc\nhost=127.0.0.1\nport=${VNCPORT}\npassword=freedom" > "${rv_config}"

remote-viewer "${rv_config}" 2>/dev/null &
