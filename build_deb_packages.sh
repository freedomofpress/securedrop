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

#apt-key add /vagrant/install_files/ansible-base/roles/install_fpf_repo/files/fpf-signing-key.pub
#
#if [ ! -f /etc/apt/sources.list.d/fpf.list ]; then
#    echo "deb [arch=amd64] https://apt.pressfreedomfoundation.org/ trusty main" > /etc/apt/sources.list.d/fpf.list
#    apt-get update
#fi

build_meta() {
    PACKAGE_NAME="$1"
    PACKAGE_PATH="$2"
    PACKAGE_VERSION=$(grep Version $PACKAGE_PATH/DEBIAN/control | cut -d: -f2 | tr -d ' ')

    BUILD_DIR="$BUILD_PATH/$PACKAGE_NAME-$PACKAGE_VERSION-$SD_ARCH"
    if [ -d $BUILD_DIR ]; then
        rm -R $BUILD_DIR
    fi
    mkdir -p $BUILD_DIR

    cp -r $PACKAGE_PATH/DEBIAN $BUILD_DIR/DEBIAN

    # Create the deb package
    dpkg-deb --build $BUILD_DIR
    cp $BUILD_PATH/$PACKAGE_NAME-$PACKAGE_VERSION-$SD_ARCH.deb /vagrant
}

build_meta securedrop-grsec /vagrant/install_files/securedrop-grsec
exit 0
