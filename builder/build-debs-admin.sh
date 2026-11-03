#!/bin/bash
# Build securedrop-admin packages. This runs *inside* the container.

set -euxo pipefail

source /etc/os-release

# Build the package in /srv/securedrop-admin
cp -R /src/admin/ /srv/securedrop-admin/

# Copy ansible-base
cp -R /src/install_files/ansible-base /srv/securedrop-admin/

# Copy list of supported locales
cp /src/securedrop/i18n.json /srv/securedrop-admin/

# Copy keepassxc template database
cp -R /src/keepassxc /srv/securedrop-admin/

# Copy binaries
mkdir -p /srv/securedrop-admin/bin
cp /src/admin/bin/validate-gpg-key.sh /srv/securedrop-admin/bin/
cp /src/admin/bin/securedrop-admin-packaged /srv/securedrop-admin/bin/securedrop-admin

cd /srv/securedrop-admin

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
HOST_UID="${HOST_UID:-0}"
HOST_GID="${HOST_GID:-0}"
chown -R "$HOST_UID:$HOST_GID" "/src/build/${VERSION_CODENAME}"
