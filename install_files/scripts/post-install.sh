#!/bin/bash
# Usage: ./display_tor_urls.sh
# Description: Depending which SecureDrop package is installed
#  display the respective Tor URL and auth values
set -e
#set -x
bold=$(tput bold)
blue=$(tput setaf 4)
red=$(tput setaf 1)
normalcolor=$(tput sgr 0)

    if [ "$(dpkg -l securedrop-app-interfaces)" ]; then
        # Display the URLs for the Source and Document interfaces
        if [ -f /var/chroot/source/var/lib/tor/hidden_service/hostname ]; then
            source_int="$(cat /var/chroot/source/var/lib/tor/hidden_service/hostname)"
            echo "$bold$blue################################################################################$normalcolor"
            echo "$blue The Source Interface's URL is: $normalcolor"
            echo "$red http://$source_int"
        fi

        
        if [ -f /var/chroot/document/var/lib/tor/hidden_service/hostname ]; then
            echo "$blue The Document Interface listens on port 8080"
            echo " you will need to$bold append :8080$normalcolor$blue to the URL as shown below"
            echo " The Document Interface's URL and auth values for each journalist: $normalcolor"
            while read line; do
                ONION_ADDRESS="$(echo "$line" | awk '{print $1}')"
                ATHS_USER="$(echo "$line" | awk '{print $5}')"
                echo "$red $ATHS_USER$blue's URL is$red http://$ONION_ADDRESS:8080$normalcolor"
                echo "$red $ATHS_USER$blue's TBB torrc config line is:"
                echo "$red HidServAuth $line $normalcolor"
            done < /var/chroot/document/var/lib/tor/hidden_service/hostname
            echo "$blue To add more journalists run $red'sudo /opt/securedrop/add-journalists.sh NAME'$blue script$normalcolor"
            echo "$bold$blue################################################################################$normalcolor"
        fi

        if [ -f /var/lib/tor/hidden_service/hostname ]; then
            echo "$bold$blue#################################################################################$normalcolor"
            echo "$blue The App Server is only accessible through a Tor Authenticated Hidden Service"
            echo " you will need to use connect-proxy, torify or something similar to"
            echo " proxy SSH through Tor$normalcolor"
            while read line; do
                ONION_ADDRESS="$(echo "$line" | awk '{print $1}')"
                ATHS_USER="$(echo "$line" | awk '{print $5}')"
                echo "$red $ATHS_USER$blue's SSH address is$red ssh $ATHS_USER@$ONION_ADDRESS$normalcolor"
                echo "$red $ATHS_USER$blue's system torrc config line is:"
                echo "$red HidServAuth $line $normalcolor"
                echo "$red $ATHS_USER$blue's Google Authenticator secret key is $red$(head -1 /home/${ATHS_USER}/.google_authenticator)$normalcolor"
            done < /var/lib/tor/hidden_service/hostname
            echo "$blue You will need to run the$red 'sudo /opt/securedrop/add-admin.sh USERNAME'$blue"
            echo " to add more admins.$normalcolor"
            echo "$bold$blue#################################################################################$normalcolor"
       fi
    elif [ "$(dpkg -l securedrop-document)" ]; then
        if [ -f /var/lib/tor/hidden_service/hostname ]; then
            echo "$blue The Document Interface listens on port 8080"
            echo " you will need to$bold append :8080$normalcolor$blue to the URL as shown below"
            echo " The Document Interface's URL and auth values for each journalist: $normalcolor"
            while read line; do
                ONION_ADDRESS="$(echo "$line" | awk '{print $1}')"
                ATHS_USER="$(echo "$line" | awk '{print $5}')"
                echo "$red $ATHS_USER$blue's URL is$red http://$ONION_ADDRESS:8080$normalcolor"
                echo "$red $ATHS_USER$blue's torrc config line is:"
                echo "$red HidServAuth $line $normalcolor"
            done < /var/lib/tor/hidden_service/hostname
            echo "$bold$blue################################################################################$normalcolor"
        fi
    elif [ "$(dpkg -l securedrop-source)" ]; then
        if [ -f /var/lib/tor/hidden_service/hostname ]; then
            source_int="$(cat /var/lib/tor/hidden_service/hostname)"
            echo "$bold$blue################################################################################$normalcolor"
            echo "$blue The Source Interface's URL is: $normalcolor"
            echo "$red http://$source_int"
        fi
    elif [ "$(dpkg -l securedrop-monitor)" ]; then
        if [ -f /var/lib/tor/hidden_service/hostname ]; then
            echo "$bold$blue#################################################################################$normalcolor"
            echo "$blue The Monitor Server is only accessible through a Tor Authenticated Hidden Service"
            echo " you will need to use connect-proxy, torify or something similar to"
            echo " proxy SSH through Tor$normalcolor"
            while read line; do
                ONION_ADDRESS="$(echo "$line" | awk '{print $1}')"
                ATHS_USER="$(echo "$line" | awk '{print $5}')"
                echo "$red $ATHS_USER$blue's SSH address is$red ssh $ATHS_USER@$ONION_ADDRESS$normalcolor"
                echo "$red $ATHS_USER$blue's system torrc config line is:"
                echo "$red HidServAuth $line $normalcolor"
                echo "$red $ATHS_USER$blue's Google Authenticator secret key is $red$(head -1 /home/${ATHS_USER}/.google_authenticator)$normalcolor"
            done < /var/lib/tor/hidden_service/hostname
            echo "$blue You will need to run the$red 'sudo /opt/securedrop/add-admin.sh USERNAME'$blue"
            echo " to add more admins.$normalcolor"
            echo "$bold$blue#################################################################################$normalcolor"
 
        fi
     fi
