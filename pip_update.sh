#!/bin/bash

# Run in the virtual environment periodically to keep packages up-to-date

set -e
cd "`dirname $0`"

cd securedrop/

# Latest MAT version needs to be manually checked at https://mat.boum.org/files/
LATEST_MAT=https://mat.boum.org/files/mat-0.4.2.tar.gz

# Auto-install updated packages
sudo pip-review --auto

# pip-dump expects a requirements.txt file, so make a dummy one.
touch requirements.txt

# Dump updated version numbers to *requirements.txt
pip-dump

# pip-dump removes URLs for some reason. Put them back.
echo $LATEST_MAT | tee -a "source-requirements.txt" "document-requirements.txt" >/dev/null

rm requirements.txt
