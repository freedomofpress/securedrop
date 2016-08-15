#!/bin/bash

# Usage: ./pip_update.sh
# Run periodically to keep Python requirements up-to-date
set -e

dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
requirements_dir="${dir}/securedrop/requirements"
venv="review_env"

# This script should not be run with an active virtualenv. Calling deactivate
# does not work reliably, so instead we warn then quit.
if [[ -n $VIRTUAL_ENV ]]; then
  echo "Please deactivate your virtualenv before running this script."
  exit 1
fi

# Test if pip and virtualenv are available and install them if not
command -v pip > /dev/null
pip_installed=$?
command -v virtualenv > /dev/null
virualenv_installed=$?

if [[ $pip_installed -ne 0 ]] || [[ $virtualenv_installed -ne 0 ]]; then
  if [[ -e /etc/os-release ]] && $(grep -i "debian" /etc/os-release > /dev/null); then
    sudo apt-get install -y python-pip virtualenv
  else
    echo "This script requires pip and virtualenv to run."
    exit
  fi
fi

# Create a temporary virtualenv for the SecureDrop Python packages in our
# requirements directory
cd $requirements_dir

trap "rm -rf ${venv}" EXIT

virtualenv -p python2.7 $venv
source "${venv}/bin/activate"

# Install the most recent pip that pip-tools supports and the latest pip-tools
# (must be done in order as the former is a dependency of the latter).
pip install pip==8.1.1
pip install pip-tools

# Compile new requirements (.txt) files from our top-level dependency (.in)
# files. See http://nvie.com/posts/better-package-management/
for r in "securedrop" "test"; do
  # Maybe pip-tools will get its act together and standardize their cert-pinning
  # syntax and this line will break. One can only hope.
  pip-compile -o "${r}-requirements.txt" "${r}-requirements.in"
done
