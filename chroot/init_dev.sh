#!/bin/sh

SOURCE_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
CHROOT_DIR=$SOURCE_ROOT/.chroot

sudo mount proc $CHROOT_DIR/proc -t proc
sudo mount sys $CHROOT_DIR/sys -t sysfs
sudo mount --bind /dev $CHROOT_DIR/dev 

sudo mount $SOURCE_ROOT $CHROOT_DIR/securedrop -o bind
