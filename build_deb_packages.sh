#!/bin/bash
## Usage: ./build_deb_package.sh $SD_VERSION
## Description: Creates directory structure and link the
## correct files to correct locations. It then use
## dpkg-deb --build to create a deb package of it.
set -e
#set -x
MY_PATH="$(dirname $0)"
MY_PATH=$(cd $MY_PATH && pwd)
BUILD_PATH="$MY_PATH/build"
SD_VERSION=${1:-0.2.1}
SD_BRANCH=${2:-dev}
umask 022


##Source interface section
build_source_deb() {
    #Create directories
    SOURCE_DIR="$BUILD_PATH/source-$SD_VERSION-$SD_BRANCH"
    if [ -d $SOURCE_DIR ]; then
        rm -R $SOURCE_DIR
    fi

    mkdir -p $SOURCE_DIR/opt/securedrop/
    mkdir -p $SOURCE_DIR/var/www/
    
    # Copy the config files to the build directory
    cp -R $MY_PATH/install_files/source/* $SOURCE_DIR
    
    # Copy the install scripts to the build directory
    cp -R $MY_PATH/install_files/scripts $SOURCE_DIR/opt/securedrop/
    
    # Copy the application code to the build directory
    cp -R $MY_PATH/securedrop/ $SOURCE_DIR/var/www/
    
    gzip -9 $SOURCE_DIR/usr/share/doc/securedrop-source/changelog.Debian
    #MD5
#    find . -type f ! -regex '.*.hg.*' ! -regex '.*?debian-binary.*' ! -regex '.*?DEBIAN.*' -printf '%P ' | xargs md5sum > DEBIAN/md5sums

    # Create the deb package
    dpkg-deb --build $SOURCE_DIR
    cp $BUILD_PATH/source-$SD_VERSION-$SD_BRANCH.deb $MY_PATH/
}

build_document_deb() {
    ##Document Interface
    DOCUMENT_DIR="$BUILD_PATH/document-$SD_VERSION-$SD_BRANCH"
    if [ -d $DOCUMENT_DIR ]; then
        rm -R $DOCUMENT_DIR
    fi
    
    #Create directories
    mkdir -p $DOCUMENT_DIR/opt/securedrop
    mkdir -p $DOCUMENT_DIR/var/www
    
    # Copy the config files to the build directory
    cp -R $MY_PATH/install_files/document/* $DOCUMENT_DIR
    
    # Copy the install scripts to the build directory
    cp -R $MY_PATH/install_files/scripts $DOCUMENT_DIR/opt/securedrop/
    
    # Copy the application code to the build directory
    cp -R $MY_PATH/securedrop/ $DOCUMENT_DIR/var/www/
    
    gzip -9 $DOCUMENT_DIR/usr/share/doc/securedrop-document/changelog.Debian
    #MD5
    #find . -type f ! -regex '.*.hg.*' ! -regex '.*?debian-binary.*' ! -regex '.*?DEBIAN.*' -printf '%P ' | xargs md5sum > DEBIAN/md5sums

    # Create the deb package
    dpkg-deb --build $DOCUMENT_DIR
    cp $BUILD_PATH/document-$SD_VERSION-$SD_BRANCH.deb $MY_PATH/
}

build_app_deb() {
    APP_DIR="$BUILD_PATH/app-$SD_VERSION-$SD_BRANCH"

    if [ -d $APP_DIR ]; then
        rm -R $APP_DIR
    fi
    
    mkdir -p $APP_DIR/opt/securedrop

    cp -R $MY_PATH/install_files/app/* $APP_DIR/
    cp -R $MY_PATH/install_files/scripts $APP_DIR/opt/securedrop
    gzip -9 $APP_DIR/usr/share/doc/securedrop-app/changelog.Debian
    #MD5
    #find . -type f ! -regex '.*.hg.*' ! -regex '.*?debian-binary.*' ! -regex '.*?DEBIAN.*' -printf '%P ' | xargs md5sum > DEBIAN/md5sums

    dpkg-deb --build $APP_DIR
    cp $BUILD_PATH/app-$SD_VERSION-$SD_BRANCH.deb $MY_PATH
}

build_monitor_deb() {
    MONITOR_DIR="$BUILD_PATH/monitor-$SD_VERSION-$SD_BRANCH"

    if [ -d $MONITOR_DIR ]; then
        rm -R $MONITOR_DIR
    fi

    mkdir -p $MONITOR_DIR/opt/securedrop

    cp -R $MY_PATH/install_files/monitor/* $MONITOR_DIR/
    cp -R $MY_PATH/install_files/scripts $MONITOR_DIR/opt/securedrop
    gzip -9 $MONITOR_DIR/usr/share/doc/securedrop-monitor/changelog.Debian
    #MD5
    #find . -type f ! -regex '.*.hg.*' ! -regex '.*?debian-binary.*' ! -regex '.*?DEBIAN.*' -printf '%P ' | xargs md5sum > DEBIAN/md5sums

    dpkg-deb --build $MONITOR_DIR
    cp $BUILD_PATH/monitor-$SD_VERSION-$SD_BRANCH.deb $MY_PATH
}
main() {
    build_source_deb
    build_document_deb
    build_app_deb
    build_monitor_deb
}

main
