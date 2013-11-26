#!/bin/bash
#Install tor repo, keyring and tor 
#save tor key to disk to be copied to chroot jails later
install_tor() {
  echo ""
  echo "Installing tor on host system..."
  add-apt-repository -y "$TOR_REPO" | tee -a build.log
  catch_error $? "with add-apt-repository -y $TOR_REPO"

  if [ -f tor.asc ]; then
    rm tor.asc
  fi

  gpg --keyserver keys.gnupg.net --recv $TOR_KEY_ID | tee -a build.log
  catch_error $? "recving tor key $TOR_KEY_ID"
  gpg --output tor.asc --armor --export $TOR_KEY_FINGERPRINT | tee -a build.log
  catch_error $? "exporting tor key $TOR_KEY_FINGERPRINT"

  if [ ! "$1" = "--no-updates" ]; then
    apt-key add tor.asc | tee -a build.log
    catch_error $? "adding tor.asc"
    apt-get -y update | tee -a build.log
    apt-get -y install deb.torproject.org-keyring tor | tee -a build.log
    catch_error $? "installing deb.torproject.org-keyring and/or tor on host"
    echo "tor installed on host system"
  fi

  #This is for systems that didn't have their torrc file configured by the 
  #base_install.sh script so that
  if ! grep -Fxq '^SocksPort' /etc/tor/torrc; then
    echo "SocksPort 0" >> /etc/tor/torrc
    service tor restart | tee -a build.log
    catch_error $? "restarting tor service on host"
  fi

  #Lock the tor user account
  echo "Locking the tor user account..."
  passwd -l debian-tor | tee -a build.log
  catch_error $? "locking tor user account"
  echo "tor user account locked"
}
