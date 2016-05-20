#!/bin/bash

# Usage: ./pip_update.sh
# Run periodically to keep Python requirements up-to-date
set -e

REQUIREMENTS_DIR=$(pwd)/securedrop/requirements

# If we're in a virtualenv, deactivate it
if [[ -n $VIRTUALENV ]]; then
  deactivate
fi

# Test if pip and virtualenv are available and install them if not
command -v pip > /dev/null
pip_installed=$?
command -v virtualenv > /dev/null
virualenv_installed=$?

if [ $pip_installed -ne 0 ] || [ $virtualenv_installed -ne 0 ]; then
  if $(grep -i "debian" /etc/os-release > /dev/null); then
    sudo apt-get install -y python-pip virtualenv
  else
    echo "This script requires pip and virtualenv to run."
    exit
  fi
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
