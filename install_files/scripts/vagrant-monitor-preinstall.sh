#!/bin/bash
# Usage: (verify debconf preseed answers) ./app-preinstall.sh
# Update the debconf preseed questions at the bootom of the 
# script and the location of the app deb package to install

set -e
#set -x
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

debconf-set-selections <<< "postfix postfix/mailname string $(hostname -f)"
debconf-set-selections <<< "postfix postfix/main_mailer_type string 'Internet Site'"

debconf-set-selections << EOF
#securedrop-monitor-0.2.1-amd64.deb securedrop-monitor/get_smtp string gmail-smtp-in.l.google.com
#securedrop-monitor-0.2.1-amd64.deb securedrop-monitor/get_email string username@gmail.com
#securedrop-monitor-0.2.1-amd64.deb securedrop-monitor/get_email_from string ossec@securedrop
securedrop-monitor-0.2.1-amd64.deb securedrop-monitor/admin_user string vagrant
securedrop-monitor-0.2.1-amd64.deb securedrop-monitor/app_ip string CHANGEME
EOF

gdebi --non-interactive /vagrant/monitor-0.2.1-amd64.deb
