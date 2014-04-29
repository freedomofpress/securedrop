#!/bin/bash

if [[ $EUID -eq 0 ]]; then
    echo "Please run this as your normal user, not root"
    exit 1
fi

SOURCE_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
CHROOT_DIR=$SOURCE_ROOT/.chroot

# setup schroot 
sudo sh -c "cat $SOURCE_ROOT/chroot/schroot.conf | sed 's|SECUREDROP_LOCATION|$CHROOT_DIR|g' >> /etc/schroot/schroot.conf"

# install precise inside of the chroot
mkdir -p $CHROOT_DIR
sudo debootstrap --arch=amd64 precise $CHROOT_DIR http://archive.ubuntu.com/ubuntu/
sudo mkdir -p $CHROOT_DIR/securedrop
sudo cp $SOURCE_ROOT/chroot/sources.list $CHROOT_DIR/etc/apt/sources.list
sudo cp /etc/resolv.conf $CHROOT_DIR/etc/resolv.conf
sudo sh -c "echo '127.0.0.1 dev' >> $CHROOT_DIR/etc/hosts"

# setup securedrop dev environment
$SOURCE_ROOT/chroot/start_dev.sh
sudo schroot -c securedrop -d / -- apt-get update
sudo schroot -c securedrop -d / -- apt-get -y install wget build-essential
sudo schroot -c securedrop -d /securedrop -- ./setup_dev.sh -r /securedrop-root -u
