#!/bin/bash
# Usage: source ./add-tor-repo.sh && add-tor-repo
# Description: Downloads the tor signing key and tor keyring.
# Adds the torproject repo to the apt sources list
set -e
if [ -r /lib/lsb/init-functions ]; then
    if [ "$( lsb_release -is )" = "Debian" ]; then
        distro="$( lsb_release -c )"
    else
        distro="$( lsb_release -c | cut -f 2 )"
    fi
fi

add_tor_repo() {

    # Check for and add the tor signing key source and packages
    TOR_KEY_ID="886DDD89"
    TOR_KEY_FPR="A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89" 
    
    if ! gpg --list-key $TOR_KEY_ID; then
        gpg --keyserver keys.gnupg.net --recv $TOR_KEY_ID
        gpg --export $TOR_KEY_FPR | apt-key add -
    else 
        echo "Tor's signing key is already present"
    fi
    
    # Add the tor repo to the sources list and update the system
    if [ ! -f /etc/apt/sources.list.d/tor.list ]; then
        echo "deb     http://deb.torproject.org/torproject.org $distro main" > /etc/apt/sources.list.d/tor.list
    else
        echo "Tor's repo was already added to apt's sources"
    fi
    echo "done adding tor repo"
}


add_tor_repo
