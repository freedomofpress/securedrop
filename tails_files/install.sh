#!/bin/bash
# SecureDrop persistent setup script for Tails

set -e

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
TAILSCFG=/live/persistence/TailsData_unlocked
DOTFILES=$TAILSCFG/dotfiles
DESKTOP=$HOMEDIR/Desktop
ANSIBLE=$PERSISTENT/securedrop/install_files/ansible-base
NMDISPATCHER=/etc/NetworkManager/dispatcher.d
SSH_ALIASES=false

# check for Tails 2.x
source /etc/os-release
if [[ $TAILS_VERSION_ID =~ ^1\..* ]]; then
  echo "This script must be used on Tails version 2.x or greater." 1>&2
  exit 1
fi

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
if [ -f $ANSIBLE/app-ssh-aths ]; then
  ADMIN=true
else
  ADMIN=false
fi

mkdir -p $INSTALL_DIR

# copy icon, launchers and scripts
cp -f securedrop_icon.png $INSTALL_DIR
cp -f document.desktop $INSTALL_DIR
cp -f source.desktop $INSTALL_DIR
cp -f securedrop_init.py $SCRIPT_PY

# Remove binary setuid wrapper from previous tails_files installation, if it exists
WRAPPER_BIN=$INSTALL_DIR/securedrop_init
if [ -f $WRAPPER_BIN ]; then
    rm $WRAPPER_BIN
fi

if $ADMIN; then
  DOCUMENT=`cat $ANSIBLE/app-document-aths | cut -d ' ' -f 2`
  SOURCE=`cat $ANSIBLE/app-source-ths`
  APPSSH=`cat $ANSIBLE/app-ssh-aths | cut -d ' ' -f 2`
  MONSSH=`cat $ANSIBLE/mon-ssh-aths | cut -d ' ' -f 2`
  echo "# HidServAuth lines for SecureDrop's authenticated hidden services" | cat - $ANSIBLE/app-ssh-aths $ANSIBLE/mon-ssh-aths $ANSIBLE/app-document-aths > $ADDITIONS
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
    cp -pf $INSTALL_DIR/ssh_config $HOMEDIR/.ssh/config
    SSH_ALIASES=true
  fi
  # set ansible to auto-install
  if ! grep -q 'ansible' "$TAILSCFG/live-additional-software.conf"; then
    echo "ansible" >> $TAILSCFG/live-additional-software.conf
  fi
  # update ansible inventory with .onion hostnames
  if ! grep -v "^#.*onion" "$ANSIBLE/inventory" | grep -q onion; then
    sed -i "s/app ansible_ssh_host=.* /app ansible_ssh_host=$APPSSH /" $ANSIBLE/inventory
    sed -i "s/mon ansible_ssh_host=.* /mon ansible_ssh_host=$MONSSH /" $ANSIBLE/inventory
  fi
else
  # prepare torrc_additions (journalist)
  cp -f torrc_additions $ADDITIONS
fi

# set permissions
chmod 755 $INSTALL_DIR
chown root:root $SCRIPT_PY
chmod 700 $SCRIPT_PY
chown root:root $ADDITIONS
chmod 400 $ADDITIONS

chown amnesia:amnesia $INSTALL_DIR/securedrop_icon.png
chmod 600 $INSTALL_DIR/securedrop_icon.png

# journalist workstation does not have the *-aths files created by the Ansible playbook, so we must prompt
# to get the interface .onion addresses to setup launchers, and for the HidServAuth info used by Tor
if ! $ADMIN; then
  REGEX="^(HidServAuth [a-z2-7]{16}\.onion [A-Za-z0-9+/.]{22})"
  while [[ ! "$HIDSERVAUTH" =~ $REGEX ]];
  do
    HIDSERVAUTH=$(zenity --entry --title="Hidden service authentication setup" --width=600 --window-icon=$INSTALL_DIR/securedrop_icon.png --text="Enter the HidServAuth value to be added to /etc/tor/torrc:")
  done
  echo $HIDSERVAUTH >> $ADDITIONS
  SRC=$(zenity --entry --title="Desktop shortcut setup" --window-icon=$INSTALL_DIR/securedrop_icon.png --text="Enter the Source Interface's .onion address:")
  SOURCE="${SRC#http://}"
  DOCUMENT=`echo $HIDSERVAUTH | cut -d ' ' -f 2`
fi

# make the shortcuts
echo "Exec=/usr/local/bin/tor-browser $DOCUMENT" >> $INSTALL_DIR/document.desktop
echo "Exec=/usr/local/bin/tor-browser $SOURCE" >> $INSTALL_DIR/source.desktop

# copy launchers to desktop and Applications menu
cp -f $INSTALL_DIR/document.desktop $DESKTOP
cp -f $INSTALL_DIR/source.desktop $DESKTOP
cp -f $INSTALL_DIR/document.desktop $HOMEDIR/.local/share/applications
cp -f $INSTALL_DIR/source.desktop $HOMEDIR/.local/share/applications

# make it all persistent
sudo -u amnesia mkdir -p $DOTFILES/Desktop
sudo -u amnesia mkdir -p $DOTFILES/.local/share/applications
cp -f $INSTALL_DIR/document.desktop $DOTFILES/Desktop
cp -f $INSTALL_DIR/source.desktop $DOTFILES/Desktop
cp -f $INSTALL_DIR/document.desktop $DOTFILES/.local/share/applications
cp -f $INSTALL_DIR/source.desktop $DOTFILES/.local/share/applications

# set ownership and permissions
chown amnesia:amnesia $DESKTOP/document.desktop $DESKTOP/source.desktop \
  $DOTFILES/Desktop/document.desktop $DOTFILES/Desktop/source.desktop \
  $HOMEDIR/.local/share/applications/document.desktop $HOMEDIR/.local/share/applications/source.desktop \
  $DOTFILES/.local/share/applications/document.desktop $DOTFILES/.local/share/applications/source.desktop
chmod 700 $DESKTOP/document.desktop $DESKTOP/source.desktop \
  $DOTFILES/Desktop/document.desktop $DOTFILES/Desktop/source.desktop \
  $HOMEDIR/.local/share/applications/document.desktop $HOMEDIR/.local/share/applications/source.desktop \
  $DOTFILES/.local/share/applications/document.desktop $DOTFILES/.local/share/applications/source.desktop

# remove xsessionrc from 0.3.2 if present
XSESSION_RC=$TAILSCFG/dotfiles/.xsessionrc
if [ -f $XSESSION_RC ]; then
  rm -f $XSESSION_RC > /dev/null 2>&1

  # Repair the torrc backup, which was probably busted due to the
  # race condition between .xsessionrc and
  # /etc/NetworkManager/dispatch.d/10-tor.sh This avoids breaking
  # Tor after this script is run.
  #
  # If the Sandbox directive is on in the torrc (now that the dust
  # has settled from any race condition shenanigans), *and* there is
  # no Sandbox directive already present in the backup of the
  # original, "unmodified-by-SecureDrop" copy of the torrc used by
  # securedrop_init, then port that Sandbox directive over to avoid
  # breaking Tor by changing the Sandbox directive while it's
  # running.
  if grep -q 'Sandbox 1' /etc/tor/torrc && ! grep -q 'Sandbox 1' /etc/tor/torrc.bak; then
    echo "Sandbox 1" >> /etc/tor/torrc.bak
  fi
fi

# Remove previous NetworkManager hook if present. The "99-" prefix
# caused the hook to run later than desired.
for d in $TAILSCFG $INSTALL_DIR $NMDISPATCHER; do
  rm -f "$d/99-tor-reload.sh" > /dev/null 2>&1
done

# set up NetworkManager hook
if ! grep -q 'custom-nm-hooks' "$TAILSCFG/persistence.conf"; then
  echo "/etc/NetworkManager/dispatcher.d	source=custom-nm-hooks,link" >> $TAILSCFG/persistence.conf
fi
mkdir -p $TAILSCFG/custom-nm-hooks
cp -f 65-configure-tor-for-securedrop.sh $TAILSCFG/custom-nm-hooks
cp -f 65-configure-tor-for-securedrop.sh $NMDISPATCHER
chown root:root $TAILSCFG/custom-nm-hooks/65-configure-tor-for-securedrop.sh $NMDISPATCHER/65-configure-tor-for-securedrop.sh
chmod 755 $TAILSCFG/custom-nm-hooks/65-configure-tor-for-securedrop.sh $NMDISPATCHER/65-configure-tor-for-securedrop.sh

# set torrc and reload Tor
/usr/bin/python $INSTALL_DIR/securedrop_init.py

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
