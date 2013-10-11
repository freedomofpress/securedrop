#!/bin/bash
# 
# Requirements:
# 1. Working tails installation https://tails.boum.org
# 2. Enabled Personal Data persistant storage
#      The Local CA directory should be in this storage
#      https://tails.boum.org/doc/first_steps/persistence/index.en.html
# 3. openssl installed
# 4. ca_openssl.cnf file
# 5. gnupg2 installed
# 6. haveged should be installed
#
# This script will create a certificate authority, generate the server
#   and client SSL certificates for the journalist interface and app gpg keys
#
# Usage:
#  cd to persistent storage
#  ./viewingInstall.sh 
#  Answer the questions
#
PERSISTENT_STORAGE=`pwd`
cd $PERSISTENT_STORAGE
PWD=`pwd`
LOCAL_CA='local_ca'
CERT_EXPIRATION='365'
KEY_SIZE='4096'

#Error handling function
catch_error() {
  if [ $1 -ne "0" ]; then
    echo "ERROR encountered $2"
    exit 1
  fi
  }

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root" 1>&2
  exit 1
fi

# Create application's GPG keypair
read -p 'Create new gpg keypair for the application (y/n)? ' -e -i y CREATENEWGPGKEY

if [ $CREATENEWGPGKEY == 'y' ]; then
  if ! type -P gpg2; then                     
    echo "Requires the gnupg2 package to generate keypair"                  
    catch_error $? "checking for gpg2"
    exit 1
  else
    echo "Creating new Application's GPG keypair..."
    mkdir ./gpg_key_ring
    chmod 600 ./gpg_key_ring
    gpg2 --homedir ./gpg_key_ring --no-tty --batch --gen-key gpg_config
    gpg2 --homedir ./gpg_key_ring --output $PERSISTENT_STORAGE/secure_drop.asc --armor --export Journalist
    FINGERPRINT=`gpg2 --homedir ./gpg_key_ring --fingerprint Journalist | grep 'Key fingerprint'`
  fi
fi

echo "The application's public gpg is located at $PERSISTENT_STORAGE/secure_drop.asc"
echo "The application's gpg key's fingerprint is:"
echo "$FINGERPRINT"
exit 0
