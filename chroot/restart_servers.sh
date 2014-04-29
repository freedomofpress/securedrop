#!/bin/sh

SOURCE_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
CHROOT_DIR=$SOURCE_ROOT/.chroot

sudo schroot -c securedrop -d / -- killall python
sudo schroot -c securedrop -d /securedrop/securedrop -u dev -- python source.py &
sudo schroot -c securedrop -d /securedrop/securedrop -u dev -- python journalist.py &

