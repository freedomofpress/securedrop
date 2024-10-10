#!/bin/bash
set -euxo pipefail
# Adjust d/changelog version to suffix the codename.
# This runs *inside* the container.

source /etc/os-release
VERSION=$(dpkg-parsechangelog -S Version)

NIGHTLY="${NIGHTLY:-}"
if [[ -n $NIGHTLY ]]; then
    NEW_VERSION="${VERSION}.dev$(date +%Y%m%d%H%M%S)"
else
    NEW_VERSION=$VERSION
fi

# Ideally we'd use `dch` here but then we'd to install all of devscripts
sed -i "0,/${VERSION}/ s//${NEW_VERSION}+${VERSION_CODENAME}/" debian/changelog
