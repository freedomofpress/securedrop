#!/bin/bash
# Usage: ./add-admins.sh username
# Descriptions adds admin users
bold=$(tput bold)
blue=$(tput setaf 4)
red=$(tput setaf 1)
normalcolor=$(tput sgr 0)
depends="google-authenticator deb.torproject.org-keyring tor"
ssh_user="$1"

#TODO check user is root
#TODO check for args
#TODO check for depends

if [ ! $(getent group ssh) ]; then
    addgroup ssh
fi

if [ ! $(getent passwd $ssh_user) ]; then
    adduser \
        --gecos "SecureDrop Admin" \
        $ssh_user
fi

groups="sudo ssh"
for group in $groups; do
    if [ ! $(groups $ssh_user | awk -F ": " "{print $2}" | grep -q "$group") ]; then
        usermod -a -G $group $ssh_user
    fi
done

if [ ! -f /home/$ssh_user/.google_authenticator ]; then 
    su $ssh_user -c google-authenticator
fi

chmod 400 /home/$ssh_user/.google_authenticator

if [[ ! "$(grep "$ssh_user" /etc/tor/torrc)" ]]; then
    sed -i "/HiddenServiceAuthorizeClient/s/$/,$ssh_user/" /etc/tor/torrc
fi

service tor reload
echo "sleep 10 sec to wait for cert to be created"
sleep 10
if [ -f /var/lib/tor/hidden_service/hostname ]; then
    echo "$bold$blue################################################################################$normalcolor"
    echo "$blue SecureDrop Servers are only accessible through a Tor Authenticated Hidden Service"
    echo " you will need to use connect-proxy, torify or something similar to"
    echo " proxy ssh through tor"
    echo "$normalcolor"
    ONION_ADDRESS="$(awk '/'$ssh_user'/ {print $1}' /var/lib/tor/hidden_service/hostname)"
    AUTH_VALUE="$(awk '/'$ssh_user'/ {print $2}' /var/lib/tor/hidden_service/hostname)"
    echo "$red $ssh_user$blue's ssh ATHS address is$red $ONION_ADDRESS $normalcolor"
    echo "$red $ssh_user$blue's torrc config line is:"
    echo "$red HidServAuth $ONION_ADDRESS $AUTH_VALUE # $ssh_user$normalcolor"
    echo "$bold$blue################################################################################$normalcolor"
fi
