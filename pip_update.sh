#!/bin/bash

# Usage: ./pip_update.sh
# Run periodically to keep Python requirements up-to-date
set -e

REQUIREMENTS_DIR=$(pwd)/securedrop/requirements

# Test if pip and virtualenv are available and install them if not
if ! /usr/bin/dpkg-query --show --showformat='\r' 'python-pip'; then
  sudo apt-get install python-pip
fi

if ! pip show virtualenv>/dev/null; then
  sudo apt-get install virtualenv
fi

# Create a temporary virtualenv for the SecureDrop Python packages in our
# requirements directory
cd $REQUIREMENTS_DIR
VENV=review_env
virtualenv -p python2.7 $VENV
source $VENV/bin/activate

# Install the most recent pip that pip-tools supports and the latest pip-tools
# (must be done in order as the former is a dependency of the latter).
pip install --upgrade pip==8.1.1
pip install pip-tools

# Compile new requirements (.txt) files from our top-level dependency (.in)
# files. See http://nvie.com/posts/better-package-management/
for r in "securedrop-requirements" "test-requirements"
do
  # Maybe pip-tools will get its act together and standardize their cert-pinning
  # syntax and this line will break. One can only hope.
  pip-compile -o $r".txt" $r".in"
done

# Remove the temporary virtualenv
rm -r $VENV
