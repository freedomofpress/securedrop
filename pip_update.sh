#!/bin/bash

# Usage: ./pip_update.sh
# Run periodically to keep Python requirements up-to-date

set -e
cd `dirname $0`/securedrop/requirements

# This method is slow, because we have to:
# 1. Download all of the packages listed in *requirements.txt
# 2. Download any updated versions of these packages
# Unfortunately, it is the only way I have been able to get `pip-dump` to work.

sudo apt-get install python-pip

# Create a temporary virtualenv for the SecureDrop Python packages
#
# If we `pip-review --auto` the global pip packages, we will also get
# packages that are installed as part of Ubuntu/the Vagrant base
# image, which are not SecureDrop dependencies.
VENV=review_env
virtualenv $VENV
source review_env/bin/activate

# Install the requirements from the current lists
pip install -r securedrop-requirements.txt
pip install -r test-requirements.txt

# Auto-install updated packages
pip-review --auto

# Dump updated version numbers to *requirements.txt
pip-dump

# Remove the temporary virtualenv
rm -r $VENV
