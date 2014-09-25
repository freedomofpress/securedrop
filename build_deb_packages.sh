#!/bin/bash
## Usage: ./build_deb_package.sh

set -e
set -x
MY_PATH="$(dirname $0)"
MY_PATH=$(cd $MY_PATH && pwd)
BUILD_PATH="$MY_PATH/build"
SD_VERSION=${1:-0.3}
SD_ARCH=${2:-amd64}
umask 022

apt-get install libssl-dev python-pip python-dev  -y
pip install wheel

if [ ! -d "$BUILD_PATH" ]; then
    mkdir $BUILD_PATH
fi

build_app_deb() {
    PACKAGE_NAME="$1"
    PACKAGE_DIR="$BUILD_PATH/$PACKAGE_NAME-$SD_VERSION-$SD_ARCH"
    if [ -d $PACKAGE_DIR ]; then
        rm -R $PACKAGE_DIR
    fi

    # move the deb package to build dir
    cp -R $MY_PATH/install_files/securedrop-app/ $PACKAGE_DIR

    # move the app code to correct directory
    mkdir -p $PACKAGE_DIR/var/www
    cp -R $MY_PATH/securedrop/ $PACKAGE_DIR/var/www/

    # move pip wheel dependencies to correct location
    pip wheel -r securedrop/requirements/securedrop-requirements.txt
    mkdir -p $PACKAGE_DIR/var/securedrop
    mv wheelhouse $PACKAGE_DIR/var/securedrop/

    gzip -9 $PACKAGE_DIR/usr/share/doc/$PACKAGE_NAME/changelog.Debian

    # Create the deb package
    dpkg-deb --build $PACKAGE_DIR
    cp $BUILD_PATH/$PACKAGE_NAME-$SD_VERSION-$SD_ARCH.deb $MY_PATH/
}

build_app_deb securedrop-app
exit 0
