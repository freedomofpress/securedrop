#!/bin/bash
# Export env vars that are common across stages
# Saves a bit of copy-pasting throughout the snap-ci web gui
export vagrant_rpm="vagrant_1.7.2_x86_64.rpm"
export DO_SSH_KEYFILE_NAME="Vagrant"
export DO_SIZE="1gb"
export DO_REGION="sfo1"
