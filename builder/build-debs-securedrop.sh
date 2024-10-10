#!/bin/bash
# shellcheck disable=SC2209
# Build SecureDrop packages. This runs *inside* the container.

export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_PROGRESS_BAR=off
export CARGO_TERM_COLOR=never
export CARGO_TERM_PROGRESS_WHEN=never

set -euxo pipefail

# Make a copy of the source tree since we do destructive operations on it
cp -R /src/securedrop /srv/securedrop
cp -R /src/redwood /srv/redwood
cp /src/Cargo.lock /srv/redwood/
cd /srv/securedrop/

# Control the version of setuptools used in the default construction of virtual environments
# TODO: get rid of this when we switch to reproducible wheels
pip3 download --no-deps --require-hashes -r requirements/python3/requirements.txt --dest /tmp/requirements-download
rm -f /usr/share/python-wheels/setuptools-*.whl
mv /tmp/requirements-download/setuptools-*.whl /usr/share/python-wheels/

# Add the distro suffix to the version
bash /fixup-changelog

# Build the package
dpkg-buildpackage -us -uc

# Copy the built artifacts back and print checksums
source /etc/os-release
mkdir -p "/src/build/${VERSION_CODENAME}"
mv -v ../*.{buildinfo,changes,deb,tar.gz} "/src/build/${VERSION_CODENAME}"
cd "/src/build/${VERSION_CODENAME}"
sha256sum ./*
