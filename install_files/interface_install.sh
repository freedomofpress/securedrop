#!/bin/bash
#
# Usage: ./install-scripts
# --no-updates to run script without apt-get or pip install commands
# --force-clean to delete chroot jails. backup tor private keys prior
# --force-clean to delete chroot jails.
# --no-apparmor do not enforce the apache apparmor profile. This is a Secruity risk.
#securedrop.git
#securedrop/production_installation.sh                (installation script)
#securedrop/securedrop/                               (web app code)
#securedrop/CONFIG_OPTIONS			                  (user provided input)
#securedrop/securedrop/requirements.txt               (pip requirements)
#securedrop/install_files/                            (config files and install scripts)
#securedrop/install_files/SecureDrop.asc              (the app pub gpg key)
#securedrop/install_files/source_requirements.txt     (source chroot jail package dependencies)
#securedrop/install_files/document_requirements.txt (document interface chroot package dependencies)#
#
CWD="$(dirname $0)"
cd $CWD

source ../CONFIG_OPTIONS
source install_tor.sh
source install_chroot.sh
source install_source_specific.sh
source install_document_specific.sh

JAILS="source document"
TOR_REPO="deb     http://deb.torproject.org/torproject.org $( lsb_release -c | cut -f 2) main "
TOR_KEY_ID="886DDD89"
TOR_KEY_FINGERPRINT="A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89"
HOST_DEPENDENCIES=$(grep -vE "^\s*#" chroot-requirements.txt  | tr "\n" " ")
DISABLE_MODS='authn_file autoindex cgid env setenvif status'
ENABLE_MODS='wsgi headers rewrite'
BCRYPT_ID_SALT=""
BCRYPT_GPG_SALT=""
SECRET_KEY=""
APP_GPG_KEY=""
APP_GPG_KEY_FINGERPRINT=""
APP_FILES="../securedrop"


#Check that user is root
if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root" 1>&2
  exit 1
fi


#Catch error
catch_error() {
  if [ $1 -ne "0" ]; then
    echo "ERROR encountered $2"
    exit 1
  fi
}


#User Inputs the applications public gpg key and verifies fingerprint
if [ -f $KEY ]; then
  APP_GPG_KEY=$( basename "$KEY" )
  cp $KEY $CWD
else
  echo "Cannot find the application public gpg key: $KEY"
  echo "Exiting with errors can not find $KEY"
  exit 1
fi


APP_GPG_KEY_FINGERPRINT=$( gpg --with-colons --with-fingerprint $APP_GPG_KEY | awk -F: '$1=="fpr" {print $10;}' )
echo "Verify GPG fingerpint:"
echo $APP_GPG_KEY_FINGERPRINT
read -p "Is this information correct? (Y|N): " -e -i Y ANS
if [ $ANS = N -o $ANS = n ]; then
  exit 1
fi


#Add warning that install takes awhile
echo ""
echo "############################################"
echo "# Grab a cup of coffee                     #"
echo "# Installing the App Server takes awhile   #"
echo "# - Update the host system                 #"
echo "# - Install and configure 2 chroot jails   #"
echo "# - Install and configure the 2 interfaces #"
echo "# - Install and configure the other        #"
echo "#     interfaces dependencies              #"
echo "############################################"
echo ""
sleep 3

#Update system and install dependencies to generate bcyrpt salt
if [ ! "$1" = "--no-updates" ]; then
  apt-get update -y | tee -a build.log
  apt-get upgrade -y | tee -a build.log

  apt-get -y install $HOST_DEPENDENCIES | tee -a build.log
  catch_error $? "installing host dependencies"

fi

#Generate salts and secret key that will be used in hashing codenames
# / gpg passphrases and signing cookies
SCRYPT_ID_PEPPER=$( python gen_secret_key.py )
SCRYPT_GPG_PEPPER=$( python gen_secret_key.py )
catch_error $? "generating scrypt_pepper"
SECRET_KEY=$( python gen_secret_key.py )
catch_error $? "generating secret value for cookie signing"

install_tor

#Create the securedrop user on the host
echo "Creating the securedrop user on the host system"
groupadd -g 666 securedrop
groupadd -g 667 source
groupadd -g 668 document
useradd -u 666 -g 666 securedrop | tee -a build.log

install_chroot

install_source_specific

install_document_specific

#Copy rc.local file to host system to mount and start the needed services
#for the chroot jals
echo "Configuring rc.local"
cp host.rc.local /etc/rc.local | tee -a build.log
catch_error $? "copying rc.local to host system"

#cp and secure-delete build.logs in chroot jails
for JAIL in $JAILS; do
  echo "Copying and secure deleting chroot jail $JAIL build.log"
  cp /var/chroot/$JAIL/root/build.log $JAIL.build.log
  srm /var/chroot/$JAIL/root/build.log | tee -a build.log
done


for JAIL in $JAILS; do
  #Enable apparmor unless asked not to
  if [ ! "$1" = "--no-apparmor" ]; then
    echo "coying apparmor profile"
    cp var.chroot.$JAIL.usr.lib.apache2.mpm-worker.apache2 /etc/apparmor.d/
    echo "enforcing apparmor profile..."
    aa-enforce /etc/apparmor.d/var.chroot.$JAIL.usr.lib.apache2.mpm-worker.apache2 | tee -a build.log
  fi

  #Restart tor and wait 15 seconds for certs to be generted
  schroot -c $JAIL -u root service tor restart --directory /root
  schroot -c $JAIL -u root service apache2 restart --directory /root
  sleep 15

  #Use the generated hidden service addresses in the apache configs and restart apache
  while read line; do
    ONION_ADDRESS="$(echo "$line" | awk '{print $1}')"
    echo "Adding $ONION_ADDRESS"
    if [ $JAIL = 'source' ]; then
        PORT=80
    elif [ $JAIL = 'document' ]; then
        PORT=8080
    fi
    sed -i "/#INSERT_SERVER_ALIASES_HERE/a ServerAlias $ONION_ADDRESS:$PORT" /var/chroot/$JAIL/etc/apache2/sites-enabled/$JAIL
    sed -i "/#INSERT_ORIGIN_HERE/a Header add Access-Control-Allow-Origin http:\/\/$ONION_ADDRESS:$PORT" /var/chroot/$JAIL/etc/apache2/sites-enabled/$JAIL
  done < /var/chroot/$JAIL/var/lib/tor/hidden_service/hostname
done

#Display tor hostname auth values.
echo "Source interface's onion url is: "
echo "$(cat /var/chroot/source/var/lib/tor/hidden_service/hostname)"

echo "You will need to append ':8080' to the end of the document interface's onion url"
echo "The document interface's onion url and auth values:"
echo "$(cat /var/chroot/document/var/lib/tor/hidden_service/hostname)"

exit 0
