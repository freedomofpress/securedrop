#!/bin/bash

# check for root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root" 1>&2
    exit 1
fi

INSTALL_DIR=/home/amnesia/Persistent/.securedrop
ADDITIONS=$INSTALL_DIR/torrc_additions
SCRIPT_PY=$INSTALL_DIR/securedrop_init.py
SCRIPT_BIN=/home/amnesia/Persistent/securedrop_init

mkdir -p $INSTALL_DIR

# copy securedrop_init.py script
cp securedrop_init.py $SCRIPT_PY

# install deps and compile
apt-get update
apt-get install -y build-essential
gcc -o $SCRIPT_BIN securedrop_init.c

# prepare torrc_additions
cp torrc_additions $ADDITIONS
gedit $ADDITIONS

# set permissions
chown root:root $SCRIPT_BIN
chmod 755 $SCRIPT_BIN
chmod +s $SCRIPT_BIN
chown root:root $SCRIPT_PY
chmod 700 $SCRIPT_PY
chown root:root $ADDITIONS
chmod 400 $ADDITIONS

