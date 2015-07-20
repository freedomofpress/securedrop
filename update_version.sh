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

NEW_VERSION=$1

if [ -z "$NEW_VERSION" ]; then
  echo "You must specify the new version!"
  exit 1
fi

# Get the old version from securedrop/version.py
old_version_regex="^__version__ = '([0-9a-z.]+)'$"
[[ `cat securedrop/version.py` =~ $old_version_regex ]]
OLD_VERSION=${BASH_REMATCH[1]}

# Update the version shown to users of the web application.
sed -i "s/$OLD_VERSION/$NEW_VERSION/g" securedrop/version.py

# Update the version in the Debian packages
sed -i "s/^\(Version: \).*/\1$NEW_VERSION/" install_files/securedrop-app-code/DEBIAN/control
sed -i "s/^\(Version: 2.8.1+\).*/\1$NEW_VERSION/" install_files/securedrop-ossec-agent/DEBIAN/control
sed -i "s/^\(Version: 2.8.1+\).*/\1$NEW_VERSION/" install_files/securedrop-ossec-server/DEBIAN/control

# Update the version used by Ansible for the filename of the output of the deb building role
sed -i "s/^\(securedrop_app_code_version: \"\)[0-9a-z.]*/\1$NEW_VERSION/" install_files/ansible-base/group_vars/securedrop.yml

# Update the version that we tell people to check out in the install doc
sed -i "s/$OLD_VERSION/$NEW_VERSION/" docs/install.md

# Update the changelog
vim changelog.md

export DEBEMAIL="${DEBEMAIL:-securedrop@freedom.press}"
export DEBFULLNAME="${DEBFULLNAME:-SecureDrop Team}"

# Update the changelog in the Debian package
dch -v $NEW_VERSION -D trusty -c install_files/securedrop-app-code/usr/share/doc/securedrop-app-code/changelog.Debian

# Commit the change
# Due to `set -e`, providing an empty commit message here will cause the script to abort early.
git commit -a

# Initiate the process of creating a signed tag, using the workflow for signing with the airgapped signing key.
git tag -a $NEW_VERSION
git cat-file tag $NEW_VERSION > "$NEW_VERSION.tag"

echo
echo "[ok] Version update complete and committed."
echo "     Please continue the airgapped signing process with $TAGFILE".
echo
