#!/bin/bash

# Run periodically to keep packages up-to-date

set -e
cd "`dirname $0`"

cd securedrop/

# Auto-install updated packages
sudo pip-review --auto

# pip-dump expects a requirements.txt file, so make a dummy one.
touch requirements.txt

# Dump updated version numbers to *requirements.txt
pip-dump

rm requirements.txt
