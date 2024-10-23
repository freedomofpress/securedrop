#!/bin/bash
# shellcheck disable=SC2230

# Usage: ./update_version.sh <version> will set <version> in each version file,
# commit the changes, and create a tag.  Both the commit and the tag will have
# the message "SecureDrop <version>", which you can amend after the fact if
# need be.

set -e

# Only run this on the development environment, where dch is available
if ! which dch > /dev/null ; then
  echo 'dch is missing'
  echo 'run with securedrop/bin/dev-shell ../update_version.sh <version>'
  exit 1
fi

cd "$(git rev-parse --show-toplevel)"

# Since we may be running in a container, we may not  have access to ~/.gitconfig. So the
# repo-level git user config file must be set.
if ! grep -q '^\[user\]' .git/config; then
    echo 'Please set your git user config in .git/config and retry!'
    exit 1
fi

readonly NEW_VERSION=$1

export EDITOR=vim

if [ -z "$NEW_VERSION" ]; then
  echo "You must specify the new version!"
  exit 1
fi

if [[ $NEW_VERSION == *-rc* ]]; then
  echo "Release candidates should use the versioning 0.x.y~rcZ!"
  exit 1
fi

# Get the old version from securedrop/version.py
old_version_regex='^__version__ = "(.*)"$'
[[ "$(cat securedrop/version.py)" =~ $old_version_regex ]]
OLD_VERSION=${BASH_REMATCH[1]}

# Update setup.py
sed -i "s@version=\"$(echo "${OLD_VERSION}" | sed 's/\./\\./g')\"@version=\"$NEW_VERSION\"@g" securedrop/setup.py

# Update the version shown to users of the web application.
sed -i "s@$(echo "${OLD_VERSION}" | sed 's/\./\\./g')@$NEW_VERSION@g" securedrop/version.py

# Update the version in the Debian packages
sed -E -i "s/^(securedrop_version: \").*/\1$NEW_VERSION\"/" install_files/ansible-base/group_vars/all/securedrop

# If version doesn't have an rc designator, it's considered stable.
# The upgrade testing logic relies on this variable.
if [[ ! $NEW_VERSION == *~rc* ]]; then
    echo "${NEW_VERSION}" > molecule/shared/stable.ver
fi

# Update the changelog
sed -i "s/\(## ${OLD_VERSION}\)/## ${NEW_VERSION}\n\n\n\n\1/g" changelog.md
"$EDITOR" +5 changelog.md

export DEBEMAIL="${DEBEMAIL:-securedrop@freedom.press}"
export DEBFULLNAME="${DEBFULLNAME:-SecureDrop Team}"

# Update the changelog in the Debian package
dch -b -v "${NEW_VERSION}" -D unstable -c securedrop/debian/changelog
# Commit the change
git commit -a -m "SecureDrop ${NEW_VERSION}"

echo "[ok] Version update complete and committed."

# We use the version string 0.x.y~rcz for the release candidate deb packages but
# we use 0.x.y-rcz for the tags as "~" is an invalid character in a git tag.
if [[ $NEW_VERSION == *~* ]]; then
  # This is an rc and we should replace "~" with "-" in the tag version.
  TAG_VERSION="${NEW_VERSION//\~/\-}"
else
  # This is a stable release.
  TAG_VERSION="${NEW_VERSION}"
fi

git tag -a "${TAG_VERSION}" -m "SecureDrop ${NEW_VERSION}"
TAGFILE="${TAG_VERSION}.tag"
git cat-file tag "${TAG_VERSION}" > "${TAGFILE}"
echo "A tag has been generated: ${TAGFILE}"

# Remind the developer that in order to create a signed tag for release, they must proceed with the airgapped signing process.
echo "If you wish to release this version, please continue the airgapped signing process with the tag file."
