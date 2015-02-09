#!/bin/bash
## Usage:
##  ./build_package.sh securedrop-ossec-server
##  ./build_package.sh securedrop-ossec-agent


set -e
set -x

BUILD_PATH="/tmp/build"
SD_ARCH=${2:-amd64}
PACKAGE_NAME="$1"
PACKAGE_PATH="/vagrant/install_files/$PACKAGE_NAME"

umask 022

if [ ! -d $BUILD_PATH ]; then
    mkdir $BUILD_PATH
fi

build_generic() {
    PACKAGE_VERSION=$(grep Version $PACKAGE_PATH/DEBIAN/control | cut -d: -f2 | tr -d ' ')

    BUILD_DIR="$BUILD_PATH/$PACKAGE_NAME-$PACKAGE_VERSION-$SD_ARCH"
    if [ -d $BUILD_DIR ]; then
        rm -R $BUILD_DIR
    fi
    mkdir -p $BUILD_DIR

    cp -r $PACKAGE_PATH/* $BUILD_DIR

    # Create the deb package
    dpkg-deb --build $BUILD_DIR
    cp $BUILD_PATH/$PACKAGE_NAME-$PACKAGE_VERSION-$SD_ARCH.deb /vagrant/build
}

build_generic $PACKAGENAME $PACKAGEPATH
exit 0
