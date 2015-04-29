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
TAILSCFG=/live/persistence/TailsData_unlocked
DOTFILES=$TAILSCFG/dotfiles

# check for persistence
if [ ! -d "$TAILSCFG" ]; then
  echo "This script must be run on Tails with a persistent volume." 1>&2
  exit 1
fi

mkdir -p $INSTALL_DIR

# install deps and compile
apt-get update
apt-get install -y build-essential
gcc -o $SCRIPT_BIN securedrop_init.c

# copy init scripts
cp securedrop_init.py $SCRIPT_PY
cp 70-tor-reload.sh $INSTALL_DIR

cp securedrop_icon.png $INSTALL_DIR

# prepare torrc_additions
cp torrc_additions $ADDITIONS
gedit $ADDITIONS > /dev/null 2>&1

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
chown root:root $INSTALL_DIR/70-tor-reload.sh
chmod 755 $INSTALL_DIR/70-tor-reload.sh

# set up NetworkManager hook
if ! grep -q 'custom-nm-hooks' "$TAILSCFG/persistence.conf"; then
  echo "/etc/NetworkManager/dispatcher.d	source=custom-nm-hooks,link" >> $TAILSCFG/persistence.conf
fi
mkdir -p $TAILSCFG/custom-nm-hooks
cp -p $INSTALL_DIR/70-tor-reload.sh $TAILSCFG/custom-nm-hooks
cp -p $INSTALL_DIR/70-tor-reload.sh /etc/NetworkManager/dispatcher.d/

# run the torrc update
$INSTALL_DIR/securedrop_init

echo ""
echo "Successfully configured the persistent initialization script for SecureDrop's Tor configuration!"
echo "You will see a notification appear in the top-right corner of your screen when it runs."
echo ""
exit 0
