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
DOTFILES=/live/persistence/TailsData_unlocked/dotfiles
DESKTOP=/home/amnesia/Desktop
ANSIBLE=$PERSISTENT/securedrop/install_files/ansible-base

if [ -f $ANSIBLE/app-document-aths ]; then
	ADMIN=true
else
	ADMIN=false
fi

if $ADMIN; then
	DOCUMENT=`cat $ANSIBLE/app-document-aths | cut -d ' ' -f 1`
	SOURCE=`cat $ANSIBLE/ansible-base/app-source-ths`
fi

mkdir -p $INSTALL_DIR

# install deps and compile
apt-get update
apt-get install -y build-essential
gcc -o $SCRIPT_BIN securedrop_init.c

# copy icon and launchers
cp securedrop_icon.png $INSTALL_DIR
cp document.desktop $INSTALL_DIR
cp source.desktop $INSTALL_DIR
cp .xsessionrc $INSTALL_DIR

# copy securedrop_init.py script
cp securedrop_init.py $SCRIPT_PY

# prepare torrc_additions
cp torrc_additions $ADDITIONS

if $ADMIN; then
	cat $ANSIBLE/app-ssh-aths $ANSIBLE/mon-ssh-aths $ANSIBLE/app-document-aths >> $ADDITIONS
else
	gedit $ADDITIONS
fi

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

chown amnesia:amnesia $INSTALL_DIR/document.desktop $INSTALL_DIR/source.desktop $INSTALL_DIR/.xsessionrc
chmod 700 $INSTALL_DIR/document.desktop $INSTALL_DIR/source.desktop $INSTALL_DIR/.xsessionrc

if ! $ADMIN; then
	echo "Type the Document Interface's .onion address, then press ENTER:"
	read DOCUMENT
	echo "Type the Source Interface's .onion address, then press ENTER:"
	read SOURCE
fi

echo "Exec=/usr/local/bin/tor-browser $DOCUMENT" >> $INSTALL_DIR/document.desktop
echo "Exec=/usr/local/bin/tor-browser $SOURCE" >> $INSTALL_DIR/source.desktop

cp -p $INSTALL_DIR/document.desktop $DESKTOP
cp -p $INSTALL_DIR/source.desktop $DESKTOP
sudo -u amnesia mkdir -p $DOTFILES/Desktop
cp -p $DESKTOP/source.desktop $DOTFILES/Desktop
cp -p $DESKTOP/document.desktop $DOTFILES/Desktop
cp -p $INSTALL_DIR/.xsessionrc $DOTFILES

$INSTALL_DIR/securedrop_init

echo ""
echo "Successfully configured Tor and set up desktop bookmarks for SecureDrop!"
echo "You will see a notification appear in the top-right corner of your screen."
echo ""
