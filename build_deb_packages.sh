#!/bin/bash
## Usage: ./build_deb_package.sh

set -e
set -x
MY_PATH="$(dirname $0)"
MY_PATH=$(cd $MY_PATH && pwd)
BUILD_PATH="$MY_PATH/build"
SD_VERSION=${1:-0.2.1}
SD_ARCH=${2:-amd64}
umask 022

build_int_deb() {
    PACKAGE_DIR="$BUILD_PATH/$PACKAGE_NAME-$SD_VERSION-$SD_ARCH"
    if [ -d $PACKAGE_DIR ]; then
        rm -R $PACKAGE_DIR
    fi
    
    #Create directories
    mkdir -p $PACKAGE_DIR/var/www
    
    # Copy the config files to the build directory
    cp -R $MY_PATH/install_files/$PACKAGE_NAME/* $PACKAGE_DIR
    
    # Copy the application code to the build directory
    cp -R $MY_PATH/securedrop/ $PACKAGE_DIR/var/www/
    
    gzip -9 $PACKAGE_DIR/usr/share/doc/securedrop-$PACKAGE_NAME/changelog.Debian
    #MD5
    #find . -type f ! -regex '.*.hg.*' ! -regex '.*?debian-binary.*' ! -regex '.*?DEBIAN.*' -printf '%P ' | xargs md5sum > DEBIAN/md5sums

    # Create the deb package
    dpkg-deb --build $PACKAGE_DIR
    cp $BUILD_PATH/$PACKAGE_NAME-$SD_VERSION-$SD_ARCH.deb $MY_PATH/
}

build_deb() {
    PACKAGE_DIR="$BUILD_PATH/$PACKAGE_NAME-$SD_VERSION-$SD_ARCH"

    if [ -d $PACKAGE_DIR ]; then
        rm -R $PACKAGE_DIR
    fi

    mkdir -p $PACKAGE_DIR 
    cp -R $MY_PATH/install_files/$PACKAGE_NAME/* $PACKAGE_DIR/
    gzip -9 $PACKAGE_DIR/usr/share/doc/securedrop-$PACKAGE_NAME/changelog.Debian
    #MD5
    #find . -type f ! -regex '.*.hg.*' ! -regex '.*?debian-binary.*' ! -regex '.*?DEBIAN.*' -printf '%P ' | xargs md5sum > DEBIAN/md5sums

    dpkg-deb --build $PACKAGE_DIR
    cp $BUILD_PATH/$PACKAGE_NAME-$SD_VERSION-$SD_ARCH.deb $MY_PATH
}

interfaces="source document"
for interface in $interfaces; do
    PACKAGE_NAME=$interface
    build_int_deb
done

debs="app-interfaces app-hardening app-ossec monitor"
for deb in $debs; do
    PACKAGE_NAME=$deb
    build_deb
done

exit 0
