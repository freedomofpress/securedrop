#!/bin/bash
#
# Usage: ./production_installation.sh
#securedrop.git
#securedrop/production_installation.sh                (installation script)
#securedrop/securedrop/                               (web app code)
#securedrop/CONFIG_OPTIONS			                  (user provided input)
#securedrop/securedrop/requirements.txt               (pip requirements)
#securedrop/install_files/                            (config files and install scripts)
#securedrop/install_files/SecureDrop.asc              (the app pub gpg key)
#securedrop/install_files/source_requirements.txt     (source chroot jail package dependencies)
#securedrop/install_files/journalist_requirements.txt (journalist interface chroot package dependencies)#
#
CWD="$(dirname $0)"
source CONFIG_OPTIONS

#Error handling function
catch_error() {
  if [ $1 -ne "0" ]; then
  echo "ERROR encountered $2"
  exit 1
fi
}

#Check that user is root
if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root" 1>&2
  exit 1
fi

#Check release
if [ -f /etc/redhat-release ]; then
  DISTRO="fedora"
# Debian/Ubuntu
elif [ -r /lib/lsb/init-functions ]; then
  if [ "$( lsb_release -is )" == "Debian" ]; then
    DISTRO="debian"
    DISTRO_VERSION="$( lsb_release -c )"
  else
    DISTRO="ubuntu"
    DISTRO_VERSION="$( lsb_release -c | cut -f 2 )"
  fi
fi

echo "Performing installation on $DISTRO - $DISTRO_VERSION"

if [ $DISTRO != 'ubuntu' ]; then
  echo ""
  echo "You are installing SecurerDrop on an unsupported system."
  echo "Do you wish to continue at your own risk [Y|N]? "
  read DISTRO_ANS
  if [ $DISTRO_ANS = y -o $DISTRO_ANS = Y ]
  then
    echo "Use at your own risk"
  else
    echo "Use ubuntu precise x64"
    exit 1
  fi
fi


# Start installation scripts specific for each role
if [ "$ROLE" = 'monitor' ]; then
  echo "Starting ossec server install..."
  $CWD/install_files/ossec_install.sh
  catch_error $? "installing ossec server"
  echo "OSSEC server installed."

  echo "Starting base install..."
  $CWD/install_files/base_install.sh
  catch_error $? "installing base."
  echo "The base is installed."

  echo ""
  echo "##################################################"
  echo "# The Monitor Server's installation is complete. #"
  echo "# The Monitor Server's SSH address is below.     #"
  echo "##################################################"
  echo ""
  echo "The Monitor Server's ssh onion address and auth values are:"
  cat /var/lib/tor/hidden_service/hostname
  echo "The Monitor Server's installation is complete."

elif [ $ROLE = 'app' ]; then
  echo "Starting interface_install.sh"
  $CWD/install_files/interface_install.sh
  catch_error $? "interface install."
  echo "Interface install complete"

  echo "Starting ossec agent install..."
  $CWD/install_files/ossec_install.sh
  catch_error $? "ossec agent installation."
  echo "OSSEC agent installation complete."

  echo "Starting base installation..."
  $CWD/install_files/base_install.sh
  catch_error $? "base installation."
  echo "The base is installed"

  echo "The installation in complete."

#Output access information for the source role
  echo ""
  echo "############################################################"
  echo "# The App Server's installation is complete.               #"
  echo "# Please finish the installation on the Monitor Server.    #"
  echo "# The App Server's SSH address and interface urls are below #"
  echo "############################################################"
  echo ""

  echo "The source interfaces's Tor URL is:"
  cat /var/chroot/source/var/lib/tor/hidden_service/hostname
  echo ""
  echo "The document interface listens on port 8080"
  echo "You will need to append :8080 to the end of the Document Interface's urls."
  echo "The Document Interface's Tor URL and auth values are:"
  cat /var/chroot/document/var/lib/tor/hidden_service/hostname
  echo ""
  echo "The App Server's SSH onion address and auth values are:"
  cat /var/lib/tor/hidden_service/hostname
else
  echo "A valid ROLE is not defined in ~/securedrop/CONFIG_OPTIONS file"
  exit 1
fi

exit 0
