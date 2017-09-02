#!/bin/bash
## Usage:
##  ./build_package.sh securedrop-ossec-server
##  ./build_package.sh securedrop-ossec-agent


set -u
set -e
set -x

PACKAGE_NAME="$1"
BUILD_PATH="/tmp/build"
SD_ARCH=${2:-amd64}
PACKAGE_PATH="$BUILD_PATH/$PACKAGE_NAME"

umask 022

if [ ! -d $BUILD_PATH ]; then
    mkdir $BUILD_PATH
fi

build_generic() {
    PACKAGE_VERSION=$(grep Version "${PACKAGE_PATH}/DEBIAN/control" | cut -d: -f2 | tr -d ' ')

    BUILD_DIR="${BUILD_PATH}/${PACKAGE_NAME}-${PACKAGE_VERSION}-${SD_ARCH}"
    if [ -d "${BUILD_DIR}" ]; then
        rm -R "${BUILD_DIR}"
    fi
    mkdir -p "${BUILD_DIR}"

    cp -r "${PACKAGE_PATH}"/* "${BUILD_DIR}"

    # Create the deb package
    dpkg-deb --build "${BUILD_DIR}"
    cp "${BUILD_PATH}/${PACKAGE_NAME}-${PACKAGE_VERSION}-${SD_ARCH}.deb" /tmp
}

build_generic "${PACKAGE_NAME}" "${PACKAGE_PATH}"
exit 0
