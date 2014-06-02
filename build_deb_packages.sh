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
    PACKAGE_NAME="$1"
    PACKAGE_DIR="$BUILD_PATH/$PACKAGE_NAME-$SD_VERSION-$SD_ARCH"
    if [ -d $PACKAGE_DIR ]; then
        rm -R $PACKAGE_DIR
    fi
    
    mkdir -p $PACKAGE_DIR/var/www
    cp -R $MY_PATH/install_files/$PACKAGE_NAME/* $PACKAGE_DIR
    cp -R $MY_PATH/securedrop/ $PACKAGE_DIR/var/www/
    gzip -9 $PACKAGE_DIR/usr/share/doc/securedrop-$PACKAGE_NAME/changelog.Debian
    #MD5
    #find . -type f ! -regex '.*.hg.*' ! -regex '.*?debian-binary.*' ! -regex '.*?DEBIAN.*' -printf '%P ' | xargs md5sum > DEBIAN/md5sums

    # Create the deb package
    dpkg-deb --build $PACKAGE_DIR
    cp $BUILD_PATH/$PACKAGE_NAME-$SD_VERSION-$SD_ARCH.deb $MY_PATH/
}

build_deb() {
    PACKAGE_NAME="$1"
    PACKAGE_DIR="$BUILD_PATH/$PACKAGE_NAME-$SD_VERSION-$SD_ARCH"

    if [ -d $PACKAGE_DIR ]; then
        rm -R $PACKAGE_DIR
    fi

    mkdir -p $PACKAGE_DIR 
    cp -R $MY_PATH/install_files/$PACKAGE_NAME/* $PACKAGE_DIR/
    if [ -f $PACKAGE_DIR/usr/share/doc/securedrop-$PACKAGE_NAME/changelog.Debian ]; then
        gzip -9 $PACKAGE_DIR/usr/share/doc/securedrop-$PACKAGE_NAME/changelog.Debian
    fi
    #MD5
    #find . -type f ! -regex '.*.hg.*' ! -regex '.*?debian-binary.*' ! -regex '.*?DEBIAN.*' -printf '%P ' | xargs md5sum > DEBIAN/md5sums

    dpkg-deb --build $PACKAGE_DIR
    cp $BUILD_PATH/$PACKAGE_NAME-$SD_VERSION-$SD_ARCH.deb $MY_PATH
}

build_with_scripts() {
    PACKAGE_NAME="$1"
    PACKAGE_DIR="$BUILD_PATH/$PACKAGE_NAME-$SD_VERSION-$SD_ARCH"

    if [ -d $PACKAGE_DIR ]; then
        rm -R $PACKAGE_DIR
    fi

    mkdir -p $PACKAGE_DIR/opt/securedrop
    cp -R $MY_PATH/install_files/$PACKAGE_NAME/* $PACKAGE_DIR/
    cp -R $MY_PATH/install_files/scripts/add-repos.sh $PACKAGE_DIR/opt/securedrop
    cp -R $MY_PATH/install_files/scripts/post-install.sh $PACKAGE_DIR/opt/securedrop
    #MD5
    #find . -type f ! -regex '.*.hg.*' ! -regex '.*?debian-binary.*' ! -regex '.*?DEBIAN.*' -printf '%P ' | xargs md5sum > DEBIAN/md5sums

    dpkg-deb --build $PACKAGE_DIR
    cp $BUILD_PATH/$PACKAGE_NAME-$SD_VERSION-$SD_ARCH.deb $MY_PATH
}

build_int_deb source
build_int_deb document

build_deb app-hardening
build_deb app-ossec
build_deb monitor-hardening
build_deb app
build_deb monitor
build_with_scripts app-interfaces
build_with_scripts monitor-ossec
exit 0
