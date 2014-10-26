#!/bin/bash
## Usage: ./build_deb_package.sh

set -e
set -x
BUILD_PATH="/tmp/build"
SD_VERSION=${1:-0.3}
SD_ARCH=${2:-amd64}
umask 022

if [ ! -d $BUILD_PATH ]; then
    mkdir $BUILD_PATH
fi

apt-key add /vagrant/install_files/ansible-base/roles/common/files/fpf-signing-key.pub

if [ ! -f /etc/apt/sources.list.d/fpf.list ]; then
    echo "deb [arch=amd64] https://apt.pressfreedomfoundation.org/ trusty main" > /etc/apt/sources.list.d/fpf.list
    apt-get update
fi

build_meta() {
    PACKAGE_NAME="$1"
    PACKAGE_DIR="$BUILD_PATH/$PACKAGE_NAME-$SD_VERSION-$SD_ARCH"
    if [ -d $PACKAGE_DIR ]; then
        rm -R $PACKAGE_DIR
        mkdir -p $PACKAGE_DIR
    fi

    cp -r /vagrant/install_files/securedrop-grsec/DEBIAN $PACKAGE_DIR/DEBIAN

    # Create the deb package
    dpkg-deb --build $PACKAGE_DIR
    cp $BUILD_PATH/$PACKAGE_NAME-$SD_VERSION-$SD_ARCH.deb $MY_PATH/
}


build_meta securedrop-grsec
exit 0
