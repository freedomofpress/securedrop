#!/bin/bash
# Usage: (verify debconf preseed answers) ./app-preinstall.sh
# Update the debconf preseed questions at the bootom of the 
# script and the location of the app deb package to install
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

    if [ ! "$(gpg -q --list-key $TOR_KEY_ID 2> /dev/null)" ]; then
        gpg -q --keyserver keys.gnupg.net --recv $TOR_KEY_ID
        gpg -q --export $TOR_KEY_FPR | apt-key add -
    fi

    # Add the tor repo to the sources list and update the system
    if [ ! -f /etc/apt/sources.list.d/tor.list ]; then
        echo "deb     http://deb.torproject.org/torproject.org $distro main" > /etc/apt/sources.list.d/tor.list
    fi
}

add_tor_repo

apt-get update
apt-get install gdebi -y

# Sample app server debconf preseed questions/answers for vagrant dev environment
debconf-set-selections << EOF
securedrop-app-0.2.1-dev.deb securedrop-app/prod_dev boolean false
securedrop-app-0.2.1-dev.deb securedrop-app/source_deb string /vagrant/source-0.2.1-dev.deb
securedrop-app-0.2.1-dev.deb securedrop-app/document_deb string /vagrant/document-0.2.1-dev.deb
securedrop-app-0.2.1-dev.deb securedrop-app/find_key_path string /vagrant/securedrop/test_journalist_key.pub
securedrop-app-0.2.1-dev.deb securedrop-app/verify_fingerprint boolean true
securedrop-app-0.2.1-dev.deb securedrop-app/journalist_user string journo1
securedrop-app-0.2.1-dev.deb securedrop-app/admin_user string vagrant
securedrop-app-0.2.1-dev.deb securedrop-app/monitor_ip string CHANGEME
securedrop-app-0.2.1-dev.deb securedrop-app/use_custom_header_image boolean false
EOF

gdebi --non-interactive /vagrant/app-0.2.1-dev.deb
