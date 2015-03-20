#!/bin/bash

# check for root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root" 1>&2
    exit 1
fi

# set paths and variables
HOMEDIR=/home/amnesia
PERSISTENT=$HOMEDIR/Persistent
INSTALL_DIR=$PERSISTENT/.securedrop
ADDITIONS=$INSTALL_DIR/torrc_additions
SCRIPT_PY=$INSTALL_DIR/securedrop_init.py
SCRIPT_BIN=$INSTALL_DIR/securedrop_init
DOTFILES=/live/persistence/TailsData_unlocked/dotfiles
DESKTOP=$HOMEDIR/Desktop
ANSIBLE=$PERSISTENT/securedrop/install_files/ansible-base

# detect whether admin or journalist
if [ -f $ANSIBLE/app-document-aths ]; then
	ADMIN=true
else
	ADMIN=false
fi

mkdir -p $INSTALL_DIR

# install deps and compile
apt-get update
apt-get install -y build-essential
gcc -o $SCRIPT_BIN securedrop_init.c

# copy icon, launchers and scripts
cp securedrop_icon.png $INSTALL_DIR
cp document.desktop $INSTALL_DIR
cp source.desktop $INSTALL_DIR
cp .xsessionrc $INSTALL_DIR
cp securedrop_init.py $SCRIPT_PY

if $ADMIN; then
  DOCUMENT=`cat $ANSIBLE/app-document-aths | cut -d ' ' -f 1`
  SOURCE=`cat $ANSIBLE/app-source-ths`
  APPSSH=`cat $ANSIBLE/app-ssh-aths | cut -d ' ' -f 1`
  MONSSH=`cat $ANSIBLE/mon-ssh-aths | cut -d ' ' -f 1`
  cat $ANSIBLE/app-ssh-aths $ANSIBLE/mon-ssh-aths $ANSIBLE/app-document-aths >> $ADDITIONS
  # create SSH host aliases and make them persistent
  cat > $INSTALL_DIR/ssh_config <<EOL
Host app
  Hostname $APPSSH
  ProxyCommand connect -R remote -5 -S localhost:9050 %h %p
Host mon
  Hostname $MONSSH
  ProxyCommand connect -R remote -5 -S localhost:9050 %h %p
EOL
  chown amnesia:amnesia $INSTALL_DIR/ssh_config
  chmod 600 $INSTALL_DIR/ssh_config
	sudo -u amnesia mkdir -p $DOTFILES/.ssh  
	cp -p $INSTALL_DIR/ssh_config $DOTFILES/.ssh/config
  if [ -d "$HOMEDIR/.ssh" ]; then
    cp -p $INSTALL_DIR/ssh_config $HOMEDIR/.ssh/config
  fi
else
# prepare torrc_additions (journalist)
	cp torrc_additions $ADDITIONS
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

# get addresses (journalist)
if ! $ADMIN; then
	echo -n "Type the Document Interface's .onion address, then press ENTER: "
	read DOCUMENT
	echo -n "Type the Source Interface's .onion address, then press ENTER: "
	read SOURCE
fi

# make the shortcuts
echo "Exec=/usr/local/bin/tor-browser $DOCUMENT" >> $INSTALL_DIR/document.desktop
echo "Exec=/usr/local/bin/tor-browser $SOURCE" >> $INSTALL_DIR/source.desktop

# copy launchers to desktop
cp -p $INSTALL_DIR/document.desktop $DESKTOP
cp -p $INSTALL_DIR/source.desktop $DESKTOP

# make it all persistent
sudo -u amnesia mkdir -p $DOTFILES/Desktop
cp -p $DESKTOP/source.desktop $DOTFILES/Desktop
cp -p $DESKTOP/document.desktop $DOTFILES/Desktop
cp -p $INSTALL_DIR/.xsessionrc $DOTFILES

# set torrc and reload Tor
$INSTALL_DIR/securedrop_init

# finished
echo ""
echo "Successfully configured Tor and set up desktop bookmarks for SecureDrop!"
echo "You will see a notification appear in the top-right corner of your screen."
echo ""
echo "The Source Interfaces's Tor onion URL is: http://$SOURCE"
echo "The Document Interface's Tor onion URL is: http://$DOCUMENT"
if $ADMIN; then
	echo ""
	echo "The App Server's SSH hidden service address is:"
	echo $APPSSH
	echo "The Monitor Server's SSH hidden service address is:"
	echo $MONSSH
	echo ""
	echo "SSH aliases are set up. You can use them with 'ssh <username>@app' and 'ssh <username>@mon'"
fi
echo ""
