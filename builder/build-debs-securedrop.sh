#!/bin/bash
# shellcheck disable=SC2209
# Build SecureDrop packages. This runs *inside* the container.

export PIP_DISABLE_PIP_VERSION_CHECK=1

set -euxo pipefail

# Make a copy of the source tree since we do destructive operations on it
cp -R /src/securedrop /srv/securedrop
cd /srv/securedrop/

# Control the version of setuptools used in the default construction of virtual environments
# TODO: get rid of this when we switch to reproducible wheels
pip3 download --no-deps --require-hashes -r requirements/python3/requirements.txt --dest /tmp/requirements-download
rm -f /usr/share/python-wheels/setuptools-*.whl
mv /tmp/requirements-download/setuptools-*.whl /usr/share/python-wheels/

# Enable Rust
HOME="/root"
source "$HOME"/.cargo/env

# Build the package
dpkg-buildpackage -us -uc

# Copy the built artifacts back and print checksums
source /etc/os-release
mkdir -p /src/build/focal
mv -v ../*.{buildinfo,changes,deb,tar.gz} /src/build/focal
cd /src/build/focal
sha256sum ./*
