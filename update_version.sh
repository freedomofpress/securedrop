#!/bin/bash
## Usage: ./update_version.sh <version>

# Only run this on the Vagrant build VM, with dch and git available
command -v dch > /dev/null
dch_installed=$?
command -v git > /dev/null
git_installed=$?
if [ $dch_installed -ne 0 ] || [ $git_installed -ne 0 ]; then
  echo "You must run this on a system with dch and git available (in order to edit the Debian package changelog and commit message)"
  echo "If you are on Debian/Ubuntu, apt-get install devscripts git"
  exit 1
fi

set -e

VERSION=$1

if [ -z "$VERSION" ]; then
  echo "You must specify the new version!"
  exit 1
fi

# Set defaults the DEBEMAIL and DEBFULLNAME environment variables, used when editing the changelog. You can override these defaults by setting these variables yourself before running the script.
export DEBEMAIL="${DEBEMAIL:-securedrop@freedom.press}"
export DEBFULLNAME="${DEBFULLNAME:-SecureDrop Team}"

# Update the version shown to users of the web application.
# Note: Mac OS X's sed requires `-i ""` (a zero-length extension, indicating no backup should be made) in order to do in-place substitution.
sed -i "s/^\(__version__ = '\)[0-9a-z.]*/\1$VERSION/g" securedrop/version.py

# Update the version of the securedrop-app-code Debian package
sed -i "s/^\(Version: \).*/\1$VERSION/" install_files/securedrop-app-code/DEBIAN/control

# Update the version used by Ansible for the filename of the output of the deb building role
sed -i "s/^\(securedrop_app_code_version: \"\)[0-9a-z.]*/\1$VERSION/" install_files/ansible-base/host_vars/app.yml

# Update the changelog
dch -v $VERSION -c install_files/securedrop-app-code/usr/share/doc/securedrop-app-code/changelog.Debian

# Commit the change
# Due to `set -e`, providing an empty commit message here will cause the script to abort early.
git commit -a

# Initiate the process of creating a signed tag, using the workflow for signing with the airgapped signing key.
git tag -a $VERSION

$TAGFILE=$VERSION.tag
git cat-file tag $VERSION > $TAGFILE

echo
echo "[ok] Version update complete and committed."
echo "     Please continue the airgapped signing process with $TAGFILE".
echo
