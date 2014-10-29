#!/bin/bash

# check for root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root" 1>&2
    exit 1
fi

PERSISTENT=/home/amnesia/Persistent
INSTALL_DIR=$PERSISTENT/.securedrop
ADDITIONS=$INSTALL_DIR/torrc_additions
SCRIPT_PY=$INSTALL_DIR/securedrop_init.py
SCRIPT_BIN=$INSTALL_DIR/securedrop_init

mkdir -p $INSTALL_DIR

# install deps and compile
apt-get update
apt-get install -y build-essential
gcc -o $SCRIPT_BIN securedrop_init.c

# copy launcher and icon
cp securedrop_icon.png $INSTALL_DIR
cp SecureDrop\ Init.desktop $PERSISTENT

# copy securedrop_init.py script
cp securedrop_init.py $SCRIPT_PY

# prepare torrc_additions
cp torrc_additions $ADDITIONS
gedit $ADDITIONS

# set permissions
chmod 755 $INSTALL_DIR
chown root:root $SCRIPT_BIN
chmod 755 $SCRIPT_BIN
chmod +s $SCRIPT_BIN
chown root:root $SCRIPT_PY
chmod 700 $SCRIPT_PY
chown root:root $ADDITIONS
chmod 400 $ADDITIONS

chown amnesia:amnesia $INSTALL_DIR/securedrop_icon.png
chmod 600 $INSTALL_DIR/securedrop_icon.png
chown amnesia:amnesia $PERSISTENT/SecureDrop\ Init.desktop
chmod 700 $PERSISTENT/SecureDrop\ Init.desktop

echo ""
echo "Successfully configured the auto-launcher for the document interface!"
echo "In the future, automatically set up Tor to access the document interface by double-clicking the \"SecureDrop Init\" icon in your Persistent folder."
echo "You will see a notification appear in the top right corner of your screen when it completes."
echo ""
