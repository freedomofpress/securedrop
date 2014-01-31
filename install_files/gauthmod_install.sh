#!/bin/bash
# Reads user provided input from:
#securedrop/CONFIG_OPTIONS
#
# Usage: ./gauthmod_install.sh
#
# Installs google-authenticator-apache-module server, providing
# two-factor for journalists on the Application Server's Document Interface
#
CWD="$(dirname $0)"
cd $CWD

source ../CONFIG_OPTIONS
GAUTHMODURL="https://pressfreedomfoundation.org/securedrop-files/gauth-module.tgz"
#GAUTHMODURLSIG="https://pressfreedomfoundation.org/securedrop-files/gauth-module.tgz.sig"
#SIGNINGKEY="https://pressfreedomfoundation.org/securedrop-files/signing_key.asc"
GAUTHMODZIP="gauth-module.tgz"
TEMPDIR="/tmp/gauthmod"

# Check for root
root_check() {
  if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root" 1>&2
    exit 1
  fi
}

# Catch error
catch_error() {
  if [ $1 -ne "0" ]; then
    echo "ERROR encountered $2"
    exit 1
  fi
}

if [ $ROLE = 'monitor' -o $ROLE = 'app' ]; then
  echo "Starting the google-authenticator-apache-module installation..."
else
  echo "Role not defined in securedrop/CONFIG_OPTIONS"
  exit 1
fi

download_gauthmod() {
  if [ ! -d /tmp/gauthmod ]; then
    echo "Downloading $GAUTHMODURL..."
    mkdir -p $TEMPDIR
    catch_error $? "making $TEMPDIR"
    ( cd $TEMPDIR ; curl $GAUTHMODURL > $GAUTHMODZIP ; )
    catch_error $? "downloading $GAUTHMODURL"

#     (cd $TEMPDIR ; curl $SIGNINGKEY > $SIGNINGKEY ; )
#     catch_error $? "downloading $SIGNINGKEY"
#     gpg --import $TEMPDIR/$SIGNINGKEY
#     catch_error $? "importing $SIGNINGKEY
#     gpg --verify $GAUTHMODZIP.sig
#     catch_error $? "verifying $GAUTHMODZIP.sig"

    echo "Extracting $GAUTHMODZIP..."
    ( cd $TEMPDIR ; tar -xzf $GAUTHMODZIP ; )
    catch_error $? "extracting $TEMPDIR"
  fi
}

install_gauthmod() {
	cp $TEMPDIR/mod_authn_google.so /var/chroot/document/usr/lib/apache2/modules/
	rm -rf $TEMPDIR
}

config_gauthmod() {
  if [ $ROLE = "app" ]; then
  		mkdir -p /var/chroot/document/var/www/securedrop/keys/gauth
	for USER in $JOURNALIST_USERS; do
		touch /var/chroot/document/var/www/securedrop/keys/gauth/$USER
		gauthcode=$(cat /dev/urandom | tr -dc 'A-Z' | head -c 16) 
		gauthpw=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | head -c 10)
		echo $gauthcode > /var/chroot/document/var/www/securedrop/keys/gauth/$USER
		echo "\"PASSWORD=$gauthpw" >> /var/chroot/document/var/www/securedrop/keys/gauth/$USER
		echo ""
		echo "$USER's two-factor login information for the Document Interface: "
		echo "	Google Authenticator key: $gauthcode"
		echo "	password: $gauthpw"
	done
	echo "LoadModule authn_google_module /usr/lib/apache2/modules/mod_authn_google.so" >> /var/chroot/document/etc/apache2/mods-available/gauth.load
	schroot -q -c document -u root --directory /root &>/dev/null <<FOE
	chown -R document:document /var/www/securedrop/keys/gauth
	a2enmod gauth
	service apache2 restart
FOE
	schroot -q -c source -u root --directory /root &>/dev/null <<FOE
	a2dismod auth_basic
	service apache2 restart
FOE
		echo ""
		echo "Copy these passwords and give them to each journalist."
		echo "In Google Authenticator, they must setup a new account using the provided time-based key."
  fi
}

main() {
  root_check

  if [ "$ROLE" = 'app' ]; then
    if [ ! "$1" = "--no-updates" ]; then 
      download_gauthmod
    fi
      install_gauthmod
      config_gauthmod
  else
    echo "not a valid role"
    exit 1 
  fi

  echo "google-authenticator-apache-module installation complete"  
}

main

exit 0
