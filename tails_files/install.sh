#!/bin/bash
# SecureDrop persistent setup script for Tails 

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
TAILSCFG=/live/persistence/TailsData_unlocked
DESKTOP=$HOMEDIR/Desktop
ANSIBLE=$PERSISTENT/securedrop/install_files/ansible-base
SSH_ALIASES=false

# check for persistence
if [ ! -d "$TAILSCFG" ]; then
  echo "This script must be run on Tails with a persistent volume." 1>&2
  exit 1
fi

# check for SecureDrop git repo
if [ ! -d "$ANSIBLE" ]; then
  echo "This script must be run with SecureDrop's git repository cloned to 'securedrop' in your Persistent folder." 1>&2
  exit 1
fi

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
  DOCUMENT=`cat $ANSIBLE/app-document-aths | cut -d ' ' -f 2`
  SOURCE=`cat $ANSIBLE/app-source-ths`
  APPSSH=`cat $ANSIBLE/app-ssh-aths | cut -d ' ' -f 2`
  MONSSH=`cat $ANSIBLE/mon-ssh-aths | cut -d ' ' -f 2`
  cat $ANSIBLE/app-ssh-aths $ANSIBLE/mon-ssh-aths $ANSIBLE/app-document-aths >> $ADDITIONS
  if [[ -d "$HOMEDIR/.ssh" && ! -f "$HOMEDIR/.ssh/config" ]]; then
    # create SSH host aliases and install them
    SSHUSER=$(zenity --entry --title="Admin SSH user" --window-icon=$INSTALL_DIR/securedrop_icon.png --text="Enter your username on the App and Monitor server:")
    cat > $INSTALL_DIR/ssh_config <<EOL
Host app
  Hostname $APPSSH
  User $SSHUSER
Host mon
  Hostname $MONSSH
  User $SSHUSER
EOL
    chown amnesia:amnesia $INSTALL_DIR/ssh_config
    chmod 600 $INSTALL_DIR/ssh_config
    cp -p $INSTALL_DIR/ssh_config $HOMEDIR/.ssh/config
    SSH_ALIASES=true
  fi
  # set ansible to auto-install
  if ! grep -q 'ansible' "$TAILSCFG/live-additional-software.conf"; then
    echo "ansible" >> $TAILSCFG/live-additional-software.conf
  fi
  # update ansible inventory with .onion hostnames
  if ! grep -q onion "$ANSIBLE/inventory"; then
    sed -i "s/app ansible_ssh_host=.* /app ansible_ssh_host=$APPSSH /" $ANSIBLE/inventory
    sed -i "s/mon ansible_ssh_host=.* /mon ansible_ssh_host=$MONSSH /" $ANSIBLE/inventory
  fi
else
  # prepare torrc_additions (journalist)
  cp torrc_additions $ADDITIONS
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

# journalist workstation does not have the *-aths files created by the Ansible playbook, so we must prompt
# to get the interface .onion addresses to setup launchers, and for the HidServAuth info used by Tor
if ! $ADMIN; then
  HIDSERVAUTH=$(zenity --entry --title="Hidden service authentication setup" --width=600 --window-icon=$INSTALL_DIR/securedrop_icon.png --text="Enter the HidServAuth value to be added to /etc/tor/torrc:")
  echo $HIDSERVAUTH >> $ADDITIONS
  SRC=$(zenity --entry --title="Desktop shortcut setup" --window-icon=$INSTALL_DIR/securedrop_icon.png --text="Enter the Source Interface's .onion address:")
  SOURCE="${SRC#http://}"
  DOCUMENT=`echo $HIDSERVAUTH | cut -d ' ' -f 2`
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
echo "The Document Interface's Tor onion URL is: http://$DOCUMENT"
echo "The Source Interfaces's Tor onion URL is: http://$SOURCE"
if $ADMIN; then
  echo ""
  echo "The App Server's SSH hidden service address is:"
  echo $APPSSH
  echo "The Monitor Server's SSH hidden service address is:"
  echo $MONSSH
  if $SSH_ALIASES; then
    echo ""
    echo "SSH aliases are set up. You can use them with 'ssh app' and 'ssh mon'"
  fi
fi
echo ""
exit 0
