#!/bin/bash
## Usage: ./update_version.sh <version>

# Only run this on the Vagrant build VM, with dch and git available
set -e

# Only run this on the Vagrant build VM, with dch and git available
if [[ "$(whoami)" != 'vagrant' ]]; then
  echo 'Only run this on the Vagrant build VM!'
  exit 1
fi

# Since we're running in a VM, we won't have access to ~/.gitconfig. So the
# repo-level git user config file must be set.
$(grep -q '^\[user\]' /vagrant/.git/config) || echo 'Please set your git' \
	'user config in /vagrant/.git/config and retry!'

readonly NEW_VERSION=$1

if [ -z "$NEW_VERSION" ]; then
  echo "You must specify the new version!"
  exit 1
fi

sudo apt-get install devscripts git -qq

# Get the old version from securedrop/version.py
old_version_regex="^__version__ = '(.*)'$"
[[ `cat securedrop/version.py` =~ $old_version_regex ]]
OLD_VERSION=${BASH_REMATCH[1]}

# Update the version shown to users of the web application.
sed -i "s/$OLD_VERSION/$NEW_VERSION/g" securedrop/version.py

# Update the version in the Debian packages
sed -i "s/^\(Version: \).*/\1$NEW_VERSION/" install_files/securedrop-app-code/DEBIAN/control
sed -i "s/^\(Version: [0-9.]\++\).*/\1$NEW_VERSION/" install_files/securedrop-ossec-agent/DEBIAN/control
sed -i "s/^\(Version: [0-9.]\++\).*/\1$NEW_VERSION/" install_files/securedrop-ossec-server/DEBIAN/control
sed -i "s/^\(Version: [0-9.]\++\).*/\1$NEW_VERSION/" install_files/securedrop-keyring/DEBIAN/control

# Update the version used by Ansible for the filename of the output of the deb building role
sed -i "s/^\(securedrop_app_code_version: \"\).*/\1$NEW_VERSION\"/" install_files/ansible-base/group_vars/securedrop.yml

# Update the version that we tell people to check out in the install doc
sed -i "s/$OLD_VERSION/$NEW_VERSION/" docs/set_up_admin_tails.rst
sed -i "s/$OLD_VERSION/$NEW_VERSION/" docs/conf.py

# Update the changelog
sed -i 's/\(## '$OLD_VERSION'\)/## '$NEW_VERSION'\n\n\n\n\1/g' changelog.md
vim +5 changelog.md

export DEBEMAIL="${DEBEMAIL:-securedrop@freedom.press}"
export DEBFULLNAME="${DEBFULLNAME:-SecureDrop Team}"

# Update the changelog in the Debian package
dch -b -v $NEW_VERSION -D trusty -c install_files/securedrop-app-code/usr/share/doc/securedrop-app-code/changelog.Debian

# Commit the change
# Due to `set -e`, providing an empty commit message here will cause the script to abort early.
git commit -a

# Initiate the process of creating a signed tag, using the workflow for signing with the airgapped signing key.
git tag -a $NEW_VERSION
TAGFILE="$NEW_VERSION.tag"
git cat-file tag $NEW_VERSION > $TAGFILE

echo
echo "[ok] Version update complete and committed."
echo "     Please continue the airgapped signing process with the tag file: $TAGFILE"
echo
